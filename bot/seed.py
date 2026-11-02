"""Demo products so the bot is not empty on the first run."""
from __future__ import annotations

from .db import Database

DEMO_PRODUCTS = [
    ("Кружка керамическая", "Белая, 300 мл", 850),
    ("Футболка", "Хлопок, размеры S-XL", 1900),
    ("Блокнот A5", "100 листов в клетку", 450),
]


async def seed_demo(db: Database) -> None:
    if await db.list_products():
        return
    for name, description, price_cents in DEMO_PRODUCTS:
        await db.add_product(name, description, price_cents)
