"""Clerk JWT verification middleware for FastAPI."""

from __future__ import annotations

import os
import json
import time
from typing import Optional
from functools import lru_cache

import jwt
import httpx
from fastapi import Request, HTTPException

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")

# Extract the Clerk instance ID from publishable key for JWKS URL
# pk_test_xxx... -> the frontend domain
_JWKS_CACHE = {"keys": [], "fetched_at": 0}


def _get_clerk_frontend_api():
    """Derive the Clerk frontend API URL from the publishable key."""
    if not CLERK_PUBLISHABLE_KEY or CLERK_PUBLISHABLE_KEY == "pk_test_PLACEHOLDER":
        return None
    # pk_test_<base64 of frontend api domain>
    import base64
    try:
        encoded = CLERK_PUBLISHABLE_KEY.split("_", 2)[2]
        # Add padding
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += "=" * padding
        domain = base64.b64decode(encoded).decode("utf-8").rstrip("$")
        return f"https://{domain}"
    except Exception:
        return None


async def _fetch_jwks():
    """Fetch Clerk's JWKS (JSON Web Key Set) for token verification."""
    now = time.time()
    if _JWKS_CACHE["keys"] and now - _JWKS_CACHE["fetched_at"] < 3600:
        return _JWKS_CACHE["keys"]

    frontend_api = _get_clerk_frontend_api()
    if not frontend_api:
        return []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{frontend_api}/.well-known/jwks.json", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            _JWKS_CACHE["keys"] = data.get("keys", [])
            _JWKS_CACHE["fetched_at"] = now
            return _JWKS_CACHE["keys"]
    except Exception as e:
        print(f"Failed to fetch JWKS: {e}")
        return _JWKS_CACHE["keys"]  # return stale cache if available


async def verify_clerk_token(request: Request) -> Optional[dict]:
    """Verify a Clerk session token from the Authorization header.

    Returns the decoded JWT claims if valid, None if no token present.
    Raises HTTPException if token is invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    if not token:
        return None

    # If Clerk isn't configured, skip verification in dev
    if CLERK_PUBLISHABLE_KEY == "pk_test_PLACEHOLDER":
        return {"sub": "dev_user", "plan": "free"}

    jwks = await _fetch_jwks()
    if not jwks:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    try:
        # Get the signing key
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        signing_key = None
        for key in jwks:
            if key.get("kid") == kid:
                signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break

        if not signing_key:
            raise HTTPException(status_code=401, detail="Invalid token signing key")

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return claims

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def require_auth(request: Request) -> dict:
    """Require a valid Clerk session. Returns claims or raises 401."""
    claims = await verify_clerk_token(request)
    if claims is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return claims
