"""Database connection pool."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Optional
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/pokescope")

pool: Optional[AsyncConnectionPool] = None


async def open_pool() -> None:
    global pool
    pool = AsyncConnectionPool(DATABASE_URL, min_size=2, max_size=10)
    await pool.open()


async def close_pool() -> None:
    if pool:
        await pool.close()


@asynccontextmanager
async def get_conn():
    async with pool.connection() as conn:
        yield conn
