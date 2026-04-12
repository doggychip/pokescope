"""Stripe subscription management."""

from __future__ import annotations

import os
from typing import Optional

import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Price IDs — create these in Stripe Dashboard or via API
# We'll auto-create them on first run
PRODUCTS = {
    "pro": {
        "name": "PokéScope Pro",
        "description": "AI analysis, scarcity deep dives, portfolio tracker, price alerts",
        "price_monthly": 1200,  # $12.00 in cents
    },
    "dealer": {
        "name": "PokéScope Dealer",
        "description": "Bulk valuation, inventory management, API access, white-label",
        "price_monthly": 4900,  # $49.00 in cents
    },
}

_price_ids: dict = {}


async def ensure_products() -> dict:
    """Create Stripe products and prices if they don't exist. Returns price ID map."""
    global _price_ids
    if _price_ids:
        return _price_ids

    if not stripe.api_key or stripe.api_key == "":
        return {}

    for tier, config in PRODUCTS.items():
        # Search for existing product
        products = stripe.Product.search(query=f'metadata["tier"]:"{tier}"')
        if products.data:
            product = products.data[0]
        else:
            product = stripe.Product.create(
                name=config["name"],
                description=config["description"],
                metadata={"tier": tier},
            )

        # Search for existing price
        prices = stripe.Price.list(product=product.id, active=True)
        if prices.data:
            price = prices.data[0]
        else:
            price = stripe.Price.create(
                product=product.id,
                unit_amount=config["price_monthly"],
                currency="usd",
                recurring={"interval": "month"},
            )

        _price_ids[tier] = price.id

    return _price_ids


async def create_checkout_session(
    tier: str,
    clerk_user_id: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a Stripe Checkout Session. Returns the checkout URL."""
    price_ids = await ensure_products()
    price_id = price_ids.get(tier)
    if not price_id:
        raise ValueError(f"Unknown tier: {tier}")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=clerk_user_id,
        metadata={"clerk_user_id": clerk_user_id, "tier": tier},
    )
    return session.url


async def create_portal_session(stripe_customer_id: str, return_url: str) -> str:
    """Create a Stripe Customer Portal session for managing subscriptions."""
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url


def get_customer_subscription(stripe_customer_id: str) -> Optional[dict]:
    """Get the active subscription for a customer."""
    if not stripe_customer_id:
        return None
    subs = stripe.Subscription.list(customer=stripe_customer_id, status="active", limit=1)
    if not subs.data:
        return None
    sub = subs.data[0]
    # Determine tier from product metadata
    price = sub["items"]["data"][0]["price"]
    product = stripe.Product.retrieve(price["product"])
    tier = product.metadata.get("tier", "pro")
    return {"tier": tier, "status": sub.status, "current_period_end": sub.current_period_end}
