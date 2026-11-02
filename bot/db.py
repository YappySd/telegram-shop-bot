"""SQLite storage built on aiosqlite. Money is stored as integer cents."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price_cents INTEGER NOT NULL CHECK (price_cents > 0)
);
CREATE TABLE IF NOT EXISTS cart (
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    qty INTEGER NOT NULL DEFAULT 1 CHECK (qty > 0),
    PRIMARY KEY (user_id, product_id)
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    total_cents INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    qty INTEGER NOT NULL
);
"""


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    description: str
    price_cents: int


@dataclass(frozen=True)
class CartLine:
    product_id: int
    name: str
    price_cents: int
    qty: int

    @property
    def subtotal_cents(self) -> int:
        return self.price_cents * self.qty


@dataclass(frozen=True)
class Order:
    id: int
    user_id: int
    username: str | None
    total_cents: int
    status: str
    lines: list[CartLine] = field(default_factory=list)


class Database:
    def __init__(self, path: str) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None
        # Prevents two simultaneous checkouts of the same cart from creating duplicate orders.
        self._order_lock = asyncio.Lock()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._conn

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    # --- products -------------------------------------------------------

    async def add_product(self, name: str, description: str, price_cents: int) -> int:
        cur = await self.conn.execute(
            "INSERT INTO products (name, description, price_cents) VALUES (?, ?, ?)",
            (name, description, price_cents),
        )
        await self.conn.commit()
        return int(cur.lastrowid)

    async def list_products(self) -> list[Product]:
        cur = await self.conn.execute(
            "SELECT id, name, description, price_cents FROM products ORDER BY id"
        )
        return [Product(**dict(row)) for row in await cur.fetchall()]

    async def get_product(self, product_id: int) -> Product | None:
        cur = await self.conn.execute(
            "SELECT id, name, description, price_cents FROM products WHERE id = ?",
            (product_id,),
        )
        row = await cur.fetchone()
        return Product(**dict(row)) if row else None

    # --- cart -----------------------------------------------------------

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        await self.conn.execute(
            """
            INSERT INTO cart (user_id, product_id, qty) VALUES (?, ?, 1)
            ON CONFLICT(user_id, product_id) DO UPDATE SET qty = qty + 1
            """,
            (user_id, product_id),
        )
        await self.conn.commit()

    async def get_cart(self, user_id: int) -> list[CartLine]:
        cur = await self.conn.execute(
            """
            SELECT p.id AS product_id, p.name AS name, p.price_cents AS price_cents, c.qty AS qty
            FROM cart c JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ? ORDER BY p.id
            """,
            (user_id,),
        )
        return [CartLine(**dict(row)) for row in await cur.fetchall()]

    async def clear_cart(self, user_id: int) -> None:
        await self.conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    # --- orders ---------------------------------------------------------

    async def create_order(self, user_id: int, username: str | None) -> Order | None:
        """Turn the user's cart into an order. Returns None if the cart is empty."""
        async with self._order_lock:
            lines = await self.get_cart(user_id)
            if not lines:
                return None
            total = sum(line.subtotal_cents for line in lines)
            try:
                cur = await self.conn.execute(
                    "INSERT INTO orders (user_id, username, total_cents) VALUES (?, ?, ?)",
                    (user_id, username, total),
                )
                order_id = int(cur.lastrowid)
                await self.conn.executemany(
                    "INSERT INTO order_items (order_id, product_id, name, price_cents, qty) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [(order_id, l.product_id, l.name, l.price_cents, l.qty) for l in lines],
                )
                await self.conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
                await self.conn.commit()
            except Exception:
                await self.conn.rollback()
                raise
            return Order(order_id, user_id, username, total, "new", lines)

    async def list_orders(self, limit: int = 10) -> list[Order]:
        cur = await self.conn.execute(
            "SELECT id, user_id, username, total_cents, status FROM orders "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        orders: list[Order] = []
        for row in await cur.fetchall():
            items_cur = await self.conn.execute(
                "SELECT product_id, name, price_cents, qty FROM order_items WHERE order_id = ?",
                (row["id"],),
            )
            lines = [CartLine(**dict(r)) for r in await items_cur.fetchall()]
            orders.append(Order(lines=lines, **dict(row)))
        return orders
