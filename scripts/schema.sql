CREATE TABLE IF NOT EXISTS cards (
    id          TEXT PRIMARY KEY,          -- e.g. "base1-4"
    name        TEXT NOT NULL,
    supertype   TEXT,                      -- Pokémon, Trainer, Energy
    subtypes    TEXT[],                    -- Basic, Stage 1, EX, etc.
    types       TEXT[],                    -- Fire, Water, etc.
    hp          INT,
    set_name    TEXT,
    set_series  TEXT,
    rarity      TEXT,
    artist      TEXT,
    image_small TEXT,
    image_large TEXT,
    raw         JSONB,                     -- full API response for future use
    search_vec  TSVECTOR,
    -- market intelligence fields
    number      TEXT,                      -- card number in set e.g. "#100/101"
    era         TEXT,                      -- WOTC, Gold Star, e-Series, Promo, Modern
    lang        TEXT DEFAULT 'EN',         -- EN, JP
    grade       TEXT,                      -- PSA 10, PSA 9, BGS 10 GL, etc.
    price       INT,                       -- current market price in USD
    fair_value  INT,                       -- estimated fair value
    psa10_pop   INT,                       -- PSA 10 population count
    psa9_pop    INT,                       -- PSA 9 population count
    price_6mo   INT,                       -- price 6 months ago
    price_12mo  INT,                       -- price 12 months ago
    social_score INT,                      -- social media buzz 0-100
    bubble      NUMERIC(4,2)              -- bubble risk score -1.0 to 1.0
);

-- Trigger to keep search_vec up to date
CREATE OR REPLACE FUNCTION cards_search_vec_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vec :=
        setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(array_to_string(NEW.types, ' '), '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.supertype, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.set_name, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_cards_search_vec ON cards;
CREATE TRIGGER trg_cards_search_vec
    BEFORE INSERT OR UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION cards_search_vec_update();

CREATE INDEX IF NOT EXISTS idx_cards_search ON cards USING GIN (search_vec);
CREATE INDEX IF NOT EXISTS idx_cards_name   ON cards (lower(name));
