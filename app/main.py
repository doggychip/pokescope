"""PokéScope — Pokémon card search API."""

import os
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.db import open_pool, close_pool, get_conn
from app.models import Card, SearchResult

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
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


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
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Card not found"})
        return row_to_card(r)
