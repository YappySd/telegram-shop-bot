from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import texts
from .db import Product


class ProductCb(CallbackData, prefix="p"):
    id: int


class AddCb(CallbackData, prefix="add"):
    id: int


class CartCb(CallbackData, prefix="cart"):
    action: str  # "checkout" | "clear"


class MenuCb(CallbackData, prefix="menu"):
    action: str  # "catalog"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.BTN_CATALOG), KeyboardButton(text=texts.BTN_CART)]],
        resize_keyboard=True,
    )


def catalog(products: list[Product]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(
            text=f"{p.name} — {texts.money(p.price_cents)}", callback_data=ProductCb(id=p.id)
        )
    builder.adjust(1)
    return builder.as_markup()


def product(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ В корзину", callback_data=AddCb(id=product_id))
    builder.button(text="⬅️ Назад", callback_data=MenuCb(action="catalog"))
    builder.adjust(1)
    return builder.as_markup()


def cart() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Оформить заказ", callback_data=CartCb(action="checkout"))
    builder.button(text="🗑 Очистить", callback_data=CartCb(action="clear"))
    builder.button(text="⬅️ В каталог", callback_data=MenuCb(action="catalog"))
    builder.adjust(1)
    return builder.as_markup()
