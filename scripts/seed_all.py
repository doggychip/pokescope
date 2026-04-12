"""Seed all downloaded cards from scripts/seed_data/page_*.json into Postgres."""

import glob
import json
import os
import random
import psycopg
from bubble import compute_bubble

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/pokescope")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "seed_data")


def classify_era(set_series):
    series = (set_series or "").lower()
    if series in ("base", "gym", "neo", "other"):
        return "WOTC"
    if series in ("e-card",):
        return "e-Series"
    if series in ("ex", "pop"):
        return "Gold Star"
    if series in ("diamond & pearl", "platinum", "heartgold & soulsilver",
                   "black & white", "bw"):
        return "Classic"
    if series in ("xy", "sun & moon", "sword & shield", "scarlet & violet",
                   "sv", "sm", "swsh"):
        return "Modern"
    if "promo" in series:
        return "Promo"
    return "Classic"


def generate_market_data(card, rarity, set_series):
    """Generate synthetic market data for a card."""
    random.seed(hash(card["id"]))
    era = classify_era(set_series)
    is_holo = rarity and "Holo" in rarity
    is_rare = rarity and ("Rare" in rarity or "Secret" in rarity or "Ultra" in rarity
                          or "Illustration" in rarity)
    is_vintage = era in ("WOTC", "e-Series", "Gold Star")

    # Price tiers based on rarity and era
    if is_holo and is_vintage:
        base_price = random.randint(500, 8000)
    elif is_rare and is_vintage:
        base_price = random.randint(200, 3000)
    elif is_holo:
        base_price = random.randint(100, 1500)
    elif is_rare:
        base_price = random.randint(50, 800)
    else:
        base_price = random.randint(5, 200)

    psa10_pop = random.randint(20, 8000)
    if is_vintage:
        psa10_pop = random.randint(10, 500)
    psa9_pop = psa10_pop * random.randint(2, 7)

    fair_value = int(base_price * random.uniform(0.75, 1.35))
    price_12mo = int(base_price * random.uniform(0.4, 0.95))
    price_6mo = int(base_price * random.uniform(0.6, 1.15))
    social_score = random.randint(15, 98)
    if is_holo:
        social_score = max(social_score, random.randint(50, 98))

    bubble = compute_bubble(base_price, fair_value, price_12mo, social_score, psa10_pop)

    return {
        "era": era,
        "grade": random.choice(["PSA 10", "PSA 9", "PSA 9", "PSA 8", "PSA 10"]),
        "price": base_price,
        "fair_value": fair_value,
        "psa10_pop": psa10_pop,
        "psa9_pop": psa9_pop,
        "price_6mo": price_6mo,
        "price_12mo": price_12mo,
        "social_score": social_score,
        "bubble": bubble,
    }


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "page_*.json")))
    if not files:
        print("No data files found. Run download_all.sh first.")
        return

    total_inserted = 0

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for path in files:
                with open(path) as f:
                    data = json.load(f)
                batch = data.get("data", [])
                if not batch:
                    continue

                for card in batch:
                    images = card.get("images", {})
                    card_set = card.get("set", {})
                    rarity = card.get("rarity")
                    set_series = card_set.get("series")
                    number = card.get("number")
                    market = generate_market_data(card, rarity, set_series)

                    cur.execute(
                        """
                        INSERT INTO cards (id, name, supertype, subtypes, types, hp,
                                           set_name, set_series, rarity, artist,
                                           image_small, image_large, raw,
                                           number, era, lang, grade,
                                           price, fair_value, psa10_pop, psa9_pop,
                                           price_6mo, price_12mo, social_score, bubble)
                        VALUES (%(id)s, %(name)s, %(supertype)s, %(subtypes)s, %(types)s,
                                %(hp)s, %(set_name)s, %(set_series)s, %(rarity)s, %(artist)s,
                                %(image_small)s, %(image_large)s, %(raw)s,
                                %(number)s, %(era)s, 'EN', %(grade)s,
                                %(price)s, %(fair_value)s, %(psa10_pop)s, %(psa9_pop)s,
                                %(price_6mo)s, %(price_12mo)s, %(social_score)s, %(bubble)s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            supertype = EXCLUDED.supertype,
                            subtypes = EXCLUDED.subtypes,
                            types = EXCLUDED.types,
                            hp = EXCLUDED.hp,
                            set_name = EXCLUDED.set_name,
                            set_series = EXCLUDED.set_series,
                            rarity = EXCLUDED.rarity,
                            artist = EXCLUDED.artist,
                            image_small = EXCLUDED.image_small,
                            image_large = EXCLUDED.image_large,
                            raw = EXCLUDED.raw,
                            number = EXCLUDED.number,
                            era = COALESCE(cards.era, EXCLUDED.era),
                            grade = COALESCE(cards.grade, EXCLUDED.grade),
                            price = COALESCE(cards.price, EXCLUDED.price),
                            fair_value = COALESCE(cards.fair_value, EXCLUDED.fair_value),
                            psa10_pop = COALESCE(cards.psa10_pop, EXCLUDED.psa10_pop),
                            psa9_pop = COALESCE(cards.psa9_pop, EXCLUDED.psa9_pop),
                            price_6mo = COALESCE(cards.price_6mo, EXCLUDED.price_6mo),
                            price_12mo = COALESCE(cards.price_12mo, EXCLUDED.price_12mo),
                            social_score = COALESCE(cards.social_score, EXCLUDED.social_score),
                            bubble = COALESCE(cards.bubble, EXCLUDED.bubble)
                        """,
                        {
                            "id": card["id"],
                            "name": card["name"],
                            "supertype": card.get("supertype"),
                            "subtypes": card.get("subtypes"),
                            "types": card.get("types"),
                            "hp": int(card["hp"]) if card.get("hp", "").isdigit() else None,
                            "set_name": card_set.get("name"),
                            "set_series": set_series,
                            "rarity": rarity,
                            "artist": card.get("artist"),
                            "image_small": images.get("small"),
                            "image_large": images.get("large"),
                            "raw": psycopg.types.json.Jsonb(card),
                            "number": number,
                            "era": market["era"],
                            "grade": market["grade"],
                            "price": market["price"],
                            "fair_value": market["fair_value"],
                            "psa10_pop": market["psa10_pop"],
                            "psa9_pop": market["psa9_pop"],
                            "price_6mo": market["price_6mo"],
                            "price_12mo": market["price_12mo"],
                            "social_score": market["social_score"],
                            "bubble": market["bubble"],
                        },
                    )

                total_inserted += len(batch)
                print(f"  {os.path.basename(path)}: {len(batch)} cards (total: {total_inserted})")

        conn.commit()
    print(f"\nDone! {total_inserted} cards inserted/updated.")


if __name__ == "__main__":
    main()
