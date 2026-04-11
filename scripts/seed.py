"""Fetch Pokémon cards from the PokémonTCG API and insert into Postgres.

Usage:
    python -m scripts.seed              # seed from local JSON files in scripts/
    python -m scripts.seed --fetch      # fetch from API first, then seed
"""

import glob
import json
import os
import subprocess
import sys
import time
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/pokescope")
API_BASE = "https://api.pokemontcg.io/v2/cards"
PAGE_SIZE = 50
MAX_RETRIES = 3
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_and_save() -> list[dict]:
    """Fetch cards from the API and save to local JSON files."""
    cards = []
    page = 1
    while True:
        url = f"{API_BASE}?page={page}&pageSize={PAGE_SIZE}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"Fetching page {page} (attempt {attempt})...")
                result = subprocess.run(
                    ["curl", "-s", "--http1.1", "--max-time", "60", url],
                    capture_output=True, text=True, timeout=90,
                )
                if not result.stdout.strip():
                    raise RuntimeError("Empty response")
                data = json.loads(result.stdout)
                break
            except Exception as e:
                if attempt == MAX_RETRIES:
                    raise
                print(f"  Retrying: {e}")
                time.sleep(2 * attempt)

        batch = data.get("data", [])
        if not batch:
            break

        out_path = os.path.join(SCRIPT_DIR, f"seed_data_{page}.json")
        with open(out_path, "w") as f:
            json.dump(data, f)

        cards.extend(batch)
        total = data.get("totalCount", 0)
        print(f"  Got {len(batch)} cards (total so far: {len(cards)}/{total})")
        if len(cards) >= total:
            break
        page += 1
        time.sleep(1)
    return cards


def load_local() -> list[dict]:
    """Load cards from local seed_data_*.json files."""
    cards = []
    files = sorted(glob.glob(os.path.join(SCRIPT_DIR, "seed_data_*.json")))
    if not files:
        print("No local seed files found. Run with --fetch first.")
        sys.exit(1)
    for path in files:
        with open(path) as f:
            data = json.load(f)
        batch = data.get("data", [])
        cards.extend(batch)
        print(f"  Loaded {len(batch)} cards from {os.path.basename(path)}")
    return cards


def insert_cards(cards: list[dict]) -> None:
    """Insert cards into Postgres, upserting on conflict."""
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for card in cards:
                images = card.get("images", {})
                card_set = card.get("set", {})
                cur.execute(
                    """
                    INSERT INTO cards (id, name, supertype, subtypes, types, hp,
                                       set_name, set_series, rarity, artist,
                                       image_small, image_large, raw)
                    VALUES (%(id)s, %(name)s, %(supertype)s, %(subtypes)s, %(types)s,
                            %(hp)s, %(set_name)s, %(set_series)s, %(rarity)s, %(artist)s,
                            %(image_small)s, %(image_large)s, %(raw)s)
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
                        raw = EXCLUDED.raw
                    """,
                    {
                        "id": card["id"],
                        "name": card["name"],
                        "supertype": card.get("supertype"),
                        "subtypes": card.get("subtypes"),
                        "types": card.get("types"),
                        "hp": int(card["hp"]) if card.get("hp", "").isdigit() else None,
                        "set_name": card_set.get("name"),
                        "set_series": card_set.get("series"),
                        "rarity": card.get("rarity"),
                        "artist": card.get("artist"),
                        "image_small": images.get("small"),
                        "image_large": images.get("large"),
                        "raw": psycopg.types.json.Jsonb(card),
                    },
                )
        conn.commit()


def main() -> None:
    print("=== PokéScope Seed ===")
    if "--fetch" in sys.argv:
        cards = fetch_and_save()
    else:
        cards = load_local()
    print(f"\n{len(cards)} cards loaded. Inserting into database...")
    insert_cards(cards)
    print("Done!")


if __name__ == "__main__":
    main()
