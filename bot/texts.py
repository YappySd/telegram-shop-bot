"""All user-facing strings live here, so the bot is easy to translate or rebrand."""
from __future__ import annotations

from html import escape

from .db import CartLine, Order, Product

CURRENCY = "$"

BTN_CATALOG = "📦 Каталог"
BTN_CART = "🛒 Корзина"

WELCOME = "Привет! Это демо-магазин. Выбери раздел в меню ниже."
CATALOG_TITLE = "Каталог. Выбери товар:"
CATALOG_EMPTY = "Каталог пока пуст."
NOT_FOUND = "Товар не найден."
ADDED = "Добавлено в корзину"
CART_EMPTY = "Корзина пуста."
CART_CLEARED = "Корзина очищена."
ORDER_PLACED = "Заказ №{order_id} оформлен. Сумма: <b>{total}</b>. Мы скоро свяжемся с тобой."
NO_ACCESS = "Эта команда только для администраторов."
ADD_USAGE = "Формат: /add Название | Цена | Описание\nНапример: /add Кружка | 8.50 | Белая, 300 мл"
NO_ORDERS = "Заказов пока нет."


def money(cents: int) -> str:
    return f"{cents / 100:.2f} {CURRENCY}"


def product_card(product: Product) -> str:
    description = f"\n\n{escape(product.description)}" if product.description else ""
    return f"<b>{escape(product.name)}</b>{description}\n\nЦена: <b>{money(product.price_cents)}</b>"


def cart_text(lines: list[CartLine]) -> str:
    rows = [f"{escape(l.name)} × {l.qty} — {money(l.subtotal_cents)}" for l in lines]
    total = sum(l.subtotal_cents for l in lines)
    return "<b>Корзина</b>\n\n" + "\n".join(rows) + f"\n\nИтого: <b>{money(total)}</b>"


def order_summary(order: Order) -> str:
    who = f"@{escape(order.username)}" if order.username else f"id {order.user_id}"
    rows = [f"{escape(l.name)} × {l.qty} — {money(l.subtotal_cents)}" for l in order.lines]
    return (
        f"<b>Заказ №{order.id}</b>\nОт: {who}\n\n"
        + "\n".join(rows)
        + f"\n\nИтого: <b>{money(order.total_cents)}</b>"
    )
