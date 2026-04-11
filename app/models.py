"""Pydantic response models."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class Card(BaseModel):
    id: str
    name: str
    supertype: Optional[str] = None
    subtypes: Optional[List[str]] = None
    types: Optional[List[str]] = None
    hp: Optional[int] = None
    set_name: Optional[str] = None
    set_series: Optional[str] = None
    rarity: Optional[str] = None
    artist: Optional[str] = None
    image_small: Optional[str] = None
    image_large: Optional[str] = None
    number: Optional[str] = None
    era: Optional[str] = None
    lang: Optional[str] = None
    grade: Optional[str] = None
    price: Optional[int] = None
    fair_value: Optional[int] = None
    psa10_pop: Optional[int] = None
    psa9_pop: Optional[int] = None
    price_6mo: Optional[int] = None
    price_12mo: Optional[int] = None
    social_score: Optional[int] = None
    bubble: Optional[float] = None


class SearchResult(BaseModel):
    query: str
    total: int
    cards: List[Card]
