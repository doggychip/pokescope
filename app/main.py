"""PokéScope — Pokémon card search API."""

import os
from contextlib import asynccontextmanager
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required in production

import stripe
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.db import open_pool, close_pool, get_conn
from app.models import Card, SearchResult
from app.auth import verify_clerk_token, require_auth
from app.payments import create_checkout_session, create_portal_session, ensure_products

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

CARD_COLUMNS = """id, name, supertype, subtypes, types, hp,
                   set_name, set_series, rarity, artist,
                   image_small, image_large,
                   number, era, lang, grade,
                   price, fair_value, psa10_pop, psa9_pop,
                   price_6mo, price_12mo, social_score, bubble"""


def row_to_card(r) -> Card:
    return Card(
        id=r[0], name=r[1], supertype=r[2], subtypes=r[3], types=r[4],
        hp=r[5], set_name=r[6], set_series=r[7], rarity=r[8],
        artist=r[9], image_small=r[10], image_large=r[11],
        number=r[12], era=r[13], lang=r[14], grade=r[15],
        price=r[16], fair_value=r[17], psa10_pop=r[18], psa9_pop=r[19],
        price_6mo=r[20], price_12mo=r[21], social_score=r[22],
        bubble=float(r[23]) if r[23] is not None else None,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_pool()
    yield
    await close_pool()


app = FastAPI(title="PokéScope", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")


@app.get("/")
async def index():
    # Serve Vite build if available, otherwise fallback to static/index.html
    for d in [FRONTEND_DIR, STATIC_DIR]:
        idx = os.path.join(d, "index.html")
        if os.path.exists(idx):
            return FileResponse(idx)
    return {"error": "No frontend build found"}


# Mount Vite build assets if available
if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/cards/search", response_model=SearchResult)
async def search_cards(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    tsquery = " & ".join(q.split())

    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT count(*) FROM cards WHERE search_vec @@ to_tsquery('english', %s)",
            (tsquery,),
        )
        total = (await row.fetchone())[0]

        rows = await conn.execute(
            f"""
            SELECT {CARD_COLUMNS}
            FROM cards
            WHERE search_vec @@ to_tsquery('english', %s)
            ORDER BY ts_rank(search_vec, to_tsquery('english', %s)) DESC
            LIMIT %s OFFSET %s
            """,
            (tsquery, tsquery, limit, offset),
        )
        cards = [row_to_card(r) for r in await rows.fetchall()]

    return SearchResult(query=q, total=total, cards=cards)


@app.get("/api/cards/market")
async def market_cards(
    sort: str = Query("bubble", description="Sort field"),
    era: Optional[str] = Query(None),
    lang: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Market intelligence endpoint — returns cards with market data, filterable and sortable."""
    conditions = ["price IS NOT NULL"]
    params: list = []

    if era:
        conditions.append("era = %s")
        params.append(era)
    if lang:
        conditions.append("lang = %s")
        params.append(lang)
    if q:
        conditions.append("search_vec @@ to_tsquery('english', %s)")
        params.append(" & ".join(q.split()))

    where = " AND ".join(conditions)

    sort_map = {
        "bubble": "bubble DESC NULLS LAST",
        "undervalued": "(price::float - fair_value::float) / NULLIF(fair_value, 0) ASC",
        "overvalued": "(price::float - fair_value::float) / NULLIF(fair_value, 0) DESC",
        "social": "social_score DESC NULLS LAST",
        "appreciation": "(price::float - price_12mo::float) / NULLIF(price_12mo, 0) DESC",
        "scarcity": "psa10_pop ASC NULLS LAST",
        "price": "price DESC",
    }
    order = sort_map.get(sort, sort_map["bubble"])

    async with get_conn() as conn:
        row = await conn.execute(
            f"SELECT count(*) FROM cards WHERE {where}", params,
        )
        total = (await row.fetchone())[0]

        rows = await conn.execute(
            f"""
            SELECT {CARD_COLUMNS}
            FROM cards WHERE {where}
            ORDER BY {order}
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        cards = [row_to_card(r) for r in await rows.fetchall()]

    return {"total": total, "cards": cards}


@app.get("/api/cards/stats")
async def market_stats():
    """Aggregate market statistics."""
    async with get_conn() as conn:
        row = await conn.execute("""
            SELECT
                count(*) FILTER (WHERE (price::float - fair_value::float) / NULLIF(fair_value, 0) < -0.15) AS undervalued,
                count(*) FILTER (WHERE (price::float - fair_value::float) / NULLIF(fair_value, 0) > 0.15) AS overvalued,
                count(*) FILTER (WHERE bubble > 0.3) AS bubble_risk,
                avg((price::float - price_12mo::float) / NULLIF(price_12mo, 0)) AS avg_return
            FROM cards WHERE price IS NOT NULL
        """)
        r = (await row.fetchone())
        return {
            "undervalued": r[0],
            "overvalued": r[1],
            "bubble_risk": r[2],
            "avg_return": round(float(r[3] or 0), 4),
        }


@app.get("/api/cards/{card_id}")
async def get_card(card_id: str):
    async with get_conn() as conn:
        row = await conn.execute(
            f"SELECT {CARD_COLUMNS} FROM cards WHERE id = %s",
            (card_id,),
        )
        r = await row.fetchone()
        if not r:
            return JSONResponse(status_code=404, content={"detail": "Card not found"})
        return row_to_card(r)


# --- Auth & Payment Endpoints ---

@app.get("/api/user/me")
async def get_current_user(request: Request):
    """Get current user info and subscription status."""
    claims = await verify_clerk_token(request)
    if claims is None:
        return {"authenticated": False, "plan": "free"}

    user_id = claims.get("sub", "")
    # In production, look up Stripe customer by clerk user ID
    # For now, return basic info
    return {
        "authenticated": True,
        "user_id": user_id,
        "plan": claims.get("plan", "free"),
    }


@app.post("/api/checkout")
async def create_checkout(request: Request):
    """Create a Stripe Checkout Session for upgrading."""
    claims = await require_auth(request)
    body = await request.json()
    tier = body.get("tier", "pro")
    user_id = claims.get("sub", "")

    if tier not in ("pro", "dealer"):
        return JSONResponse(status_code=400, content={"detail": "Invalid tier"})

    origin = str(request.base_url).rstrip("/")

    try:
        url = await create_checkout_session(
            tier=tier,
            clerk_user_id=user_id,
            success_url=f"{origin}/dashboard?upgraded=true",
            cancel_url=f"{origin}/#pricing",
        )
        return {"url": url}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.post("/api/portal")
async def customer_portal(request: Request):
    """Create a Stripe Customer Portal session for managing subscription."""
    claims = await require_auth(request)
    body = await request.json()
    customer_id = body.get("stripe_customer_id")

    if not customer_id:
        return JSONResponse(status_code=400, content={"detail": "No customer ID"})

    origin = str(request.base_url).rstrip("/")

    try:
        url = await create_portal_session(
            stripe_customer_id=customer_id,
            return_url=f"{origin}/dashboard",
        )
        return {"url": url}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for subscription lifecycle."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return JSONResponse(status_code=400, content={"detail": "Invalid signature"})
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        clerk_user_id = data.get("client_reference_id")
        customer_id = data.get("customer")
        tier = data.get("metadata", {}).get("tier", "pro")
        print(f"Checkout completed: user={clerk_user_id}, customer={customer_id}, tier={tier}")
        # TODO: Store customer_id -> clerk_user_id mapping in DB

    elif event_type == "customer.subscription.updated":
        status = data.get("status")
        customer_id = data.get("customer")
        print(f"Subscription updated: customer={customer_id}, status={status}")

    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        print(f"Subscription cancelled: customer={customer_id}")
        # TODO: Downgrade user to free plan

    return {"received": True}


# --- Seed Endpoint (for populating remote database) ---

@app.api_route("/api/admin/seed", methods=["GET", "POST"])
async def seed_database(request: Request):
    """Fetch cards from PokémonTCG API and seed into database.

    Query params:
      page: start page (default 1)
      pages: number of pages to fetch (default 5, max 20)

    Call repeatedly: /api/admin/seed?page=1, then ?page=6, ?page=11, etc.
    """
    import subprocess
    import json
    import random

    def compute_bubble(price, fair_value, price_12mo, social_score, psa10_pop):
        if not fair_value or not price_12mo:
            return 0.0
        premium = (price - fair_value) / fair_value
        momentum = (price - price_12mo) / price_12mo
        hype = (social_score / 100.0) - 0.5
        supply = min(psa10_pop / 1000.0, 1.0) - 0.3
        raw = 0.35 * premium + 0.25 * momentum + 0.20 * hype + 0.20 * supply
        return round(max(-1.0, min(1.0, raw)), 2)

    def classify_era(set_series):
        s = (set_series or "").lower()
        if s in ("base", "gym", "neo", "other"): return "WOTC"
        if s in ("e-card",): return "e-Series"
        if s in ("ex", "pop"): return "Gold Star"
        if s in ("xy", "sun & moon", "sword & shield", "scarlet & violet"): return "Modern"
        if "promo" in s: return "Promo"
        return "Classic"

    params = request.query_params
    start_page = int(params.get("page", "1"))
    max_pages = min(int(params.get("pages", "5")), 20)
    total_inserted = 0
    page = start_page
    PAGE_SIZE = 250

    async with get_conn() as conn:
        while page < start_page + max_pages:
            url = f"https://api.pokemontcg.io/v2/cards?page={page}&pageSize={PAGE_SIZE}"
            try:
                result = subprocess.run(
                    ["curl", "-s", "--max-time", "30", url],
                    capture_output=True, text=True, timeout=45,
                )
                if not result.stdout.strip():
                    break
                data = json.loads(result.stdout)
            except Exception:
                break

            batch = data.get("data", [])
            if not batch:
                break

            for card in batch:
                random.seed(hash(card["id"]))
                images = card.get("images", {})
                card_set = card.get("set", {})
                rarity = card.get("rarity")
                set_series = card_set.get("series")
                era = classify_era(set_series)
                is_holo = rarity and "Holo" in rarity
                is_vintage = era in ("WOTC", "e-Series", "Gold Star")

                if is_holo and is_vintage:
                    base_price = random.randint(500, 8000)
                elif is_holo:
                    base_price = random.randint(100, 1500)
                else:
                    base_price = random.randint(5, 200)

                psa10_pop = random.randint(10, 500) if is_vintage else random.randint(20, 8000)
                psa9_pop = psa10_pop * random.randint(2, 7)
                fair_value = int(base_price * random.uniform(0.75, 1.35))
                price_12mo = int(base_price * random.uniform(0.4, 0.95))
                price_6mo = int(base_price * random.uniform(0.6, 1.15))
                social_score = random.randint(15, 98)
                if is_holo:
                    social_score = max(social_score, random.randint(50, 98))
                bubble = compute_bubble(base_price, fair_value, price_12mo, social_score, psa10_pop)

                await conn.execute(
                    """INSERT INTO cards (id, name, supertype, subtypes, types, hp,
                        set_name, set_series, rarity, artist, image_small, image_large,
                        number, era, lang, grade, price, fair_value, psa10_pop, psa9_pop,
                        price_6mo, price_12mo, social_score, bubble)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'EN',%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO UPDATE SET
                        name=EXCLUDED.name, image_small=EXCLUDED.image_small, image_large=EXCLUDED.image_large,
                        price=COALESCE(cards.price, EXCLUDED.price), fair_value=COALESCE(cards.fair_value, EXCLUDED.fair_value)
                    """,
                    (card["id"], card["name"], card.get("supertype"), card.get("subtypes"),
                     card.get("types"), int(card["hp"]) if card.get("hp", "").isdigit() else None,
                     card_set.get("name"), set_series, rarity, card.get("artist"),
                     images.get("small"), images.get("large"),
                     card.get("number"), era,
                     random.choice(["PSA 10", "PSA 9", "PSA 8"]),
                     base_price, fair_value, psa10_pop, psa9_pop,
                     price_6mo, price_12mo, social_score, bubble),
                )

            total_inserted += len(batch)
            total_count = data.get("totalCount", 0)

            if len(batch) < PAGE_SIZE or total_inserted >= total_count:
                return {"seeded": total_inserted, "done": True, "total_in_api": total_count}
            page += 1

    return {"seeded": total_inserted, "done": False, "next_page": page, "next_url": f"/api/admin/seed?page={page}&pages={max_pages}"}


# SPA fallback — serve index.html for all non-API routes (React Router)
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    # Don't catch API or static asset routes
    if full_path.startswith("api/") or full_path.startswith("static/") or full_path.startswith("assets/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    for d in [FRONTEND_DIR, STATIC_DIR]:
        idx = os.path.join(d, "index.html")
        if os.path.exists(idx):
            return FileResponse(idx)
    return JSONResponse(status_code=404, content={"detail": "Not found"})
