import pytest

from bot.db import Database


@pytest.fixture
async def db():
    database = Database(":memory:")
    await database.connect()
    yield database
    await database.close()


async def test_products_roundtrip(db):
    pid = await db.add_product("Кружка", "Белая", 850)
    product = await db.get_product(pid)
    assert product is not None
    assert (product.name, product.price_cents) == ("Кружка", 850)
    assert [p.id for p in await db.list_products()] == [pid]
    assert await db.get_product(9999) is None


async def test_adding_same_product_twice_increases_quantity(db):
    pid = await db.add_product("Кружка", "", 850)
    await db.add_to_cart(1, pid)
    await db.add_to_cart(1, pid)
    cart = await db.get_cart(1)
    assert len(cart) == 1
    assert cart[0].qty == 2
    assert cart[0].subtotal_cents == 1700


async def test_carts_are_separate_per_user(db):
    pid = await db.add_product("Кружка", "", 850)
    await db.add_to_cart(1, pid)
    assert await db.get_cart(2) == []


async def test_checkout_creates_order_and_clears_cart(db):
    mug = await db.add_product("Кружка", "", 850)
    notebook = await db.add_product("Блокнот", "", 450)
    await db.add_to_cart(7, mug)
    await db.add_to_cart(7, mug)
    await db.add_to_cart(7, notebook)

    order = await db.create_order(7, "alice")

    assert order is not None
    assert order.total_cents == 850 * 2 + 450
    assert len(order.lines) == 2
    assert await db.get_cart(7) == []

    saved = await db.list_orders()
    assert [o.id for o in saved] == [order.id]
    assert saved[0].username == "alice"
    assert sum(l.qty for l in saved[0].lines) == 3


async def test_checkout_with_empty_cart_returns_none(db):
    assert await db.create_order(1, None) is None
    assert await db.list_orders() == []


async def test_order_keeps_price_snapshot(db):
    pid = await db.add_product("Кружка", "", 850)
    await db.add_to_cart(1, pid)
    order = await db.create_order(1, None)
    await db.conn.execute("UPDATE products SET price_cents = 9999 WHERE id = ?", (pid,))
    await db.conn.commit()
    saved = (await db.list_orders())[0]
    assert saved.id == order.id
    assert saved.total_cents == 850
    assert saved.lines[0].price_cents == 850
