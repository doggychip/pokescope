"""Database connection pool."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/pokescope")

pool: Optional[AsyncConnectionPool] = None

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    supertype   TEXT,
    subtypes    TEXT[],
    types       TEXT[],
    hp          INT,
    set_name    TEXT,
    set_series  TEXT,
    rarity      TEXT,
    artist      TEXT,
    image_small TEXT,
    image_large TEXT,
    raw         JSONB,
    search_vec  TSVECTOR,
    number      TEXT,
    era         TEXT,
    lang        TEXT DEFAULT 'EN',
    grade       TEXT,
    price       INT,
    fair_value  INT,
    psa10_pop   INT,
    psa9_pop    INT,
    price_6mo   INT,
    price_12mo  INT,
    social_score INT,
    bubble      NUMERIC(4,2)
);

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
"""


async def run_migrations() -> None:
    """Run schema migrations on startup."""
    import psycopg
    try:
        print(f"Connecting to database: {DATABASE_URL[:30]}...")
        with psycopg.connect(DATABASE_URL) as conn:
            conn.execute(SCHEMA_SQL)
            conn.commit()
        print("Database migrations complete.")
    except Exception as e:
        print(f"WARNING: Migration failed: {e}")
        print("App will start but database may not be ready.")


async def open_pool() -> None:
    global pool
    print(f"DATABASE_URL configured: {'yes' if DATABASE_URL else 'NO — set DATABASE_URL env var'}")
    await run_migrations()
    pool = AsyncConnectionPool(DATABASE_URL, min_size=1, max_size=10)
    await pool.open()
    print("Connection pool opened.")


async def close_pool() -> None:
    if pool:
        await pool.close()


@asynccontextmanager
async def get_conn():
    async with pool.connection() as conn:
        yield conn
