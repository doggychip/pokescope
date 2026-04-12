"""Seed market intelligence data — featured cards + synthetic data for existing cards."""

import os
import random
import psycopg
from bubble import compute_bubble

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/pokescope")

FEATURED_CARDS = [
    {"id": "ex11-100", "name": "Charizard Gold Star \u03b4", "set_name": "EX Dragon Frontiers", "set_series": "EX", "number": "#100/101", "era": "Gold Star", "lang": "EN", "grade": "PSA 9", "supertype": "Pok\u00e9mon", "types": ["Fire"], "hp": 100, "rarity": "Rare Holo Star", "price": 10500, "fair_value": 11000, "psa10_pop": 95, "psa9_pop": 280, "price_6mo": 8400, "price_12mo": 7200, "social_score": 94, "bubble": 0.05, "image_small": "https://images.pokemontcg.io/ex11/100.png", "image_large": "https://images.pokemontcg.io/ex11/100_hires.png"},
    {"id": "neo4-107", "name": "Shining Charizard 1st Ed", "set_name": "Neo Destiny", "set_series": "Neo", "number": "#107/105", "era": "WOTC", "lang": "EN", "grade": "PSA 9", "supertype": "Pok\u00e9mon", "types": ["Fire"], "hp": 100, "rarity": "Rare Holo", "price": 14175, "fair_value": 12000, "psa10_pop": 270, "psa9_pop": 444, "price_6mo": 11000, "price_12mo": 9500, "social_score": 91, "bubble": 0.18, "image_small": "https://images.pokemontcg.io/neo4/107.png", "image_large": "https://images.pokemontcg.io/neo4/107_hires.png"},
    {"id": "ecard2-149", "name": "Crystal Lugia", "set_name": "Aquapolis", "set_series": "e-Card", "number": "#149/147", "era": "e-Series", "lang": "EN", "grade": "PSA 9", "supertype": "Pok\u00e9mon", "types": ["Psychic"], "hp": 80, "rarity": "Rare Holo", "price": 8000, "fair_value": 10500, "psa10_pop": 138, "psa9_pop": 526, "price_6mo": 5200, "price_12mo": 3240, "social_score": 78, "bubble": -0.24, "image_small": "https://images.pokemontcg.io/ecard2/149.png", "image_large": "https://images.pokemontcg.io/ecard2/149_hires.png"},
    {"id": "ecard3-146", "name": "Crystal Charizard", "set_name": "Skyridge", "set_series": "e-Card", "number": "#146/144", "era": "e-Series", "lang": "EN", "grade": "PSA 9", "supertype": "Pok\u00e9mon", "types": ["Fire"], "hp": 100, "rarity": "Rare Holo", "price": 13500, "fair_value": 14500, "psa10_pop": 25, "psa9_pop": 180, "price_6mo": 11000, "price_12mo": 8500, "social_score": 88, "bubble": -0.07, "image_small": "https://images.pokemontcg.io/ecard3/146.png", "image_large": "https://images.pokemontcg.io/ecard3/146_hires.png"},
    {"id": "rocket-4", "name": "Dark Charizard Holo 1st Ed", "set_name": "Team Rocket", "set_series": "Base", "number": "#4/82", "era": "WOTC", "lang": "EN", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Fire"], "hp": 80, "rarity": "Rare Holo", "price": 9540, "fair_value": 8500, "psa10_pop": 554, "psa9_pop": 3489, "price_6mo": 8800, "price_12mo": 7500, "social_score": 72, "bubble": 0.12, "image_small": "https://images.pokemontcg.io/base5/4.png", "image_large": "https://images.pokemontcg.io/base5/4_hires.png"},
    {"id": "rocket-jp-6", "name": "Dark Charizard Holo", "set_name": "Rocket Gang", "set_series": "Base", "number": "#6", "era": "WOTC", "lang": "JP", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Fire"], "hp": 80, "rarity": "Rare Holo", "price": 4800, "fair_value": 3800, "psa10_pop": 1635, "psa9_pop": 4500, "price_6mo": 3500, "price_12mo": 2950, "social_score": 58, "bubble": 0.26, "image_small": "https://images.pokemontcg.io/base5/4.png", "image_large": "https://images.pokemontcg.io/base5/4_hires.png"},
    {"id": "xyp-296", "name": "Luigi Pikachu Full Art", "set_name": "XY-P Promo", "set_series": "XY", "number": "#296", "era": "Promo", "lang": "JP", "grade": "BGS 10 GL", "supertype": "Pok\u00e9mon", "types": ["Lightning"], "hp": 70, "rarity": "Promo", "price": 17000, "fair_value": 12000, "psa10_pop": 4, "psa9_pop": 35, "price_6mo": 14000, "price_12mo": 10000, "social_score": 65, "bubble": 0.42, "image_small": "https://images.pokemontcg.io/xyp/XY296.png", "image_large": "https://images.pokemontcg.io/xyp/XY296_hires.png"},
    {"id": "smp-288", "name": "Munch Pikachu", "set_name": "SM-P Promo", "set_series": "Sun & Moon", "number": "#288", "era": "Promo", "lang": "JP", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Lightning"], "hp": 60, "rarity": "Promo", "price": 8500, "fair_value": 9500, "psa10_pop": 120, "psa9_pop": 280, "price_6mo": 6800, "price_12mo": 4500, "social_score": 85, "bubble": -0.11, "image_small": "https://images.pokemontcg.io/smp/SM288.png", "image_large": "https://images.pokemontcg.io/smp/SM288_hires.png"},
    {"id": "xyp-207", "name": "Poncho Pikachu (Zard Y)", "set_name": "XY-P Promo", "set_series": "XY", "number": "#207", "era": "Promo", "lang": "JP", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Lightning"], "hp": 70, "rarity": "Promo", "price": 12000, "fair_value": 13000, "psa10_pop": 85, "psa9_pop": 200, "price_6mo": 9500, "price_12mo": 5500, "social_score": 82, "bubble": -0.08, "image_small": "https://images.pokemontcg.io/xyp/XY207.png", "image_large": "https://images.pokemontcg.io/xyp/XY207_hires.png"},
    {"id": "ex14-102", "name": "Gyarados Gold Star \u03b4", "set_name": "Holon Phantoms", "set_series": "EX", "number": "#102/110", "era": "Gold Star", "lang": "EN", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Water"], "hp": 90, "rarity": "Rare Holo Star", "price": 5000, "fair_value": 8000, "psa10_pop": 30, "psa9_pop": 95, "price_6mo": 4200, "price_12mo": 3500, "social_score": 45, "bubble": -0.38, "image_small": "https://images.pokemontcg.io/ex14/102.png", "image_large": "https://images.pokemontcg.io/ex14/102_hires.png"},
    {"id": "pop5-16", "name": "Espeon Gold Star", "set_name": "POP Series 5", "set_series": "POP", "number": "#16/17", "era": "Gold Star", "lang": "EN", "grade": "PSA 9", "supertype": "Pok\u00e9mon", "types": ["Psychic"], "hp": 70, "rarity": "Rare Holo Star", "price": 7000, "fair_value": 8500, "psa10_pop": 58, "psa9_pop": 156, "price_6mo": 5500, "price_12mo": 4000, "social_score": 76, "bubble": -0.18, "image_small": "https://images.pokemontcg.io/pop5/16.png", "image_large": "https://images.pokemontcg.io/pop5/16_hires.png"},
    {"id": "ex11-101", "name": "Mew Gold Star \u03b4", "set_name": "Dragon Frontiers", "set_series": "EX", "number": "#101/101", "era": "Gold Star", "lang": "EN", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Water"], "hp": 70, "rarity": "Rare Holo Star", "price": 6500, "fair_value": 7500, "psa10_pop": 57, "psa9_pop": 160, "price_6mo": 5200, "price_12mo": 4000, "social_score": 70, "bubble": -0.13, "image_small": "https://images.pokemontcg.io/ex11/101.png", "image_large": "https://images.pokemontcg.io/ex11/101_hires.png"},
    {"id": "swsh7-215", "name": "Umbreon VMAX Alt Art", "set_name": "Evolving Skies", "set_series": "Sword & Shield", "number": "#215/203", "era": "Modern", "lang": "EN", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Darkness"], "hp": 310, "rarity": "Secret Rare", "price": 3500, "fair_value": 4200, "psa10_pop": 2800, "psa9_pop": 4500, "price_6mo": 3200, "price_12mo": 2800, "social_score": 97, "bubble": -0.17, "image_small": "https://images.pokemontcg.io/swsh7/215.png", "image_large": "https://images.pokemontcg.io/swsh7/215_hires.png"},
    {"id": "ex6-107", "name": "Rayquaza Gold Star", "set_name": "EX Deoxys", "set_series": "EX", "number": "#107/107", "era": "Gold Star", "lang": "EN", "grade": "PSA 9", "supertype": "Pok\u00e9mon", "types": ["Colorless"], "hp": 90, "rarity": "Rare Holo Star", "price": 13000, "fair_value": 14000, "psa10_pop": 47, "psa9_pop": 130, "price_6mo": 11500, "price_12mo": 9800, "social_score": 89, "bubble": -0.07, "image_small": "https://images.pokemontcg.io/ex6/107.png", "image_large": "https://images.pokemontcg.io/ex6/107_hires.png"},
    {"id": "neo1-9", "name": "Neo Genesis Lugia 1st Ed", "set_name": "Neo Genesis", "set_series": "Neo", "number": "#9", "era": "WOTC", "lang": "EN", "grade": "PSA 9", "supertype": "Pok\u00e9mon", "types": ["Psychic"], "hp": 90, "rarity": "Rare Holo", "price": 6500, "fair_value": 9000, "psa10_pop": 45, "psa9_pop": 320, "price_6mo": 5500, "price_12mo": 4800, "social_score": 80, "bubble": -0.28, "image_small": "https://images.pokemontcg.io/neo1/9.png", "image_large": "https://images.pokemontcg.io/neo1/9_hires.png"},
    {"id": "neo4-107u", "name": "Shining Charizard Unl.", "set_name": "Neo Destiny", "set_series": "Neo", "number": "#107/105", "era": "WOTC", "lang": "EN", "grade": "PSA 9", "supertype": "Pok\u00e9mon", "types": ["Fire"], "hp": 100, "rarity": "Rare Holo", "price": 4500, "fair_value": 4200, "psa10_pop": 261, "psa9_pop": 377, "price_6mo": 4000, "price_12mo": 3500, "social_score": 62, "bubble": 0.07, "image_small": "https://images.pokemontcg.io/neo4/107.png", "image_large": "https://images.pokemontcg.io/neo4/107_hires.png"},
    {"id": "gym2-2m", "name": "Blaine's Charizard 1st Ed", "set_name": "Gym Challenge", "set_series": "Gym", "number": "#2/132", "era": "WOTC", "lang": "EN", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Fire"], "hp": 100, "rarity": "Rare Holo", "price": 7200, "fair_value": 7500, "psa10_pop": 110, "psa9_pop": 450, "price_6mo": 6000, "price_12mo": 4800, "social_score": 68, "bubble": -0.04, "image_small": "https://images.pokemontcg.io/gym2/2.png", "image_large": "https://images.pokemontcg.io/gym2/2_hires.png"},
    {"id": "sv3pt5-199", "name": "Charizard ex SIR", "set_name": "SV: 151", "set_series": "Scarlet & Violet", "number": "#199/165", "era": "Modern", "lang": "EN", "grade": "PSA 10", "supertype": "Pok\u00e9mon", "types": ["Fire"], "hp": 330, "rarity": "Special Illustration Rare", "price": 500, "fair_value": 600, "psa10_pop": 8500, "psa9_pop": 12000, "price_6mo": 450, "price_12mo": 380, "social_score": 92, "bubble": -0.17, "image_small": "https://images.pokemontcg.io/sv3pt5/199.png", "image_large": "https://images.pokemontcg.io/sv3pt5/199_hires.png"},
]


def classify_era(set_series):
    if set_series in ("Base", "Gym", "Neo"):
        return "WOTC"
    if set_series in ("e-Card",):
        return "e-Series"
    if set_series in ("EX", "POP"):
        return "Gold Star"
    if set_series in ("Diamond & Pearl", "Platinum", "HeartGold & SoulSilver"):
        return "Classic"
    if set_series in ("XY", "Sun & Moon", "Sword & Shield", "Scarlet & Violet"):
        return "Modern"
    return "Classic"


def main():
    random.seed(42)

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Insert featured cards — compute bubble from market signals
            for card in FEATURED_CARDS:
                card["bubble"] = compute_bubble(
                    card["price"], card["fair_value"], card["price_12mo"],
                    card["social_score"], card["psa10_pop"],
                )
                cur.execute("""
                    INSERT INTO cards (id, name, supertype, subtypes, types, hp,
                                       set_name, set_series, rarity, artist,
                                       image_small, image_large, number, era, lang, grade,
                                       price, fair_value, psa10_pop, psa9_pop,
                                       price_6mo, price_12mo, social_score, bubble)
                    VALUES (%(id)s, %(name)s, %(supertype)s, NULL, %(types)s, %(hp)s,
                            %(set_name)s, %(set_series)s, %(rarity)s, NULL,
                            %(image_small)s, %(image_large)s, %(number)s, %(era)s, %(lang)s, %(grade)s,
                            %(price)s, %(fair_value)s, %(psa10_pop)s, %(psa9_pop)s,
                            %(price_6mo)s, %(price_12mo)s, %(social_score)s, %(bubble)s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name, number = EXCLUDED.number, era = EXCLUDED.era,
                        lang = EXCLUDED.lang, grade = EXCLUDED.grade,
                        price = EXCLUDED.price, fair_value = EXCLUDED.fair_value,
                        psa10_pop = EXCLUDED.psa10_pop, psa9_pop = EXCLUDED.psa9_pop,
                        price_6mo = EXCLUDED.price_6mo, price_12mo = EXCLUDED.price_12mo,
                        social_score = EXCLUDED.social_score, bubble = EXCLUDED.bubble,
                        image_small = EXCLUDED.image_small, image_large = EXCLUDED.image_large,
                        set_name = EXCLUDED.set_name, set_series = EXCLUDED.set_series,
                        rarity = EXCLUDED.rarity, types = EXCLUDED.types, hp = EXCLUDED.hp
                """, card)

            print(f"  Inserted {len(FEATURED_CARDS)} featured cards")

            # Generate synthetic market data for existing cards without it
            cur.execute("SELECT id, rarity, set_series FROM cards WHERE price IS NULL")
            existing = cur.fetchall()
            for card_id, rarity, set_series in existing:
                era = classify_era(set_series or "")
                is_holo = rarity and "Holo" in rarity
                base_price = random.randint(50, 800) if not is_holo else random.randint(200, 3000)
                psa10_pop = random.randint(100, 5000)
                psa9_pop = psa10_pop * random.randint(2, 6)
                fair_value = int(base_price * random.uniform(0.8, 1.3))
                price_12mo = int(base_price * random.uniform(0.5, 0.9))
                price_6mo = int(base_price * random.uniform(0.7, 1.1))

                social_score = random.randint(20, 95)
                bubble = compute_bubble(base_price, fair_value, price_12mo, social_score, psa10_pop)

                cur.execute("""
                    UPDATE cards SET
                        era = %s, grade = %s, price = %s, fair_value = %s,
                        psa10_pop = %s, psa9_pop = %s,
                        price_6mo = %s, price_12mo = %s,
                        social_score = %s, bubble = %s
                    WHERE id = %s
                """, (
                    era,
                    random.choice(["PSA 10", "PSA 9", "PSA 8"]),
                    base_price, fair_value,
                    psa10_pop, psa9_pop,
                    price_6mo, price_12mo,
                    social_score, bubble,
                    card_id,
                ))

            print(f"  Updated {len(existing)} existing cards with synthetic market data")

        conn.commit()
    print("Done!")


if __name__ == "__main__":
    main()
