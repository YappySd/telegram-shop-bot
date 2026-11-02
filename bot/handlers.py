from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from . import keyboards as kb
from . import texts
from .config import Settings
from .db import Database
from .parsing import parse_add_args

logger = logging.getLogger(__name__)
router = Router()


# --- customer flow --------------------------------------------------------


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(texts.WELCOME, reply_markup=kb.main_menu())


@router.message(Command("catalog"))
@router.message(F.text == texts.BTN_CATALOG)
async def show_catalog(message: Message, db: Database) -> None:
    products = await db.list_products()
    if not products:
        await message.answer(texts.CATALOG_EMPTY)
        return
    await message.answer(texts.CATALOG_TITLE, reply_markup=kb.catalog(products))


@router.callback_query(kb.MenuCb.filter(F.action == "catalog"))
async def back_to_catalog(call: CallbackQuery, db: Database) -> None:
    products = await db.list_products()
    text = texts.CATALOG_TITLE if products else texts.CATALOG_EMPTY
    markup = kb.catalog(products) if products else None
    await call.message.edit_text(text, reply_markup=markup)
    await call.answer()


@router.callback_query(kb.ProductCb.filter())
async def show_product(call: CallbackQuery, callback_data: kb.ProductCb, db: Database) -> None:
    product = await db.get_product(callback_data.id)
    if product is None:
        await call.answer(texts.NOT_FOUND, show_alert=True)
        return
    await call.message.edit_text(texts.product_card(product), reply_markup=kb.product(product.id))
    await call.answer()


@router.callback_query(kb.AddCb.filter())
async def add_to_cart(call: CallbackQuery, callback_data: kb.AddCb, db: Database) -> None:
    if await db.get_product(callback_data.id) is None:
        await call.answer(texts.NOT_FOUND, show_alert=True)
        return
    await db.add_to_cart(call.from_user.id, callback_data.id)
    await call.answer(texts.ADDED)


@router.message(Command("cart"))
@router.message(F.text == texts.BTN_CART)
async def show_cart(message: Message, db: Database) -> None:
    lines = await db.get_cart(message.from_user.id)
    if not lines:
        await message.answer(texts.CART_EMPTY)
        return
    await message.answer(texts.cart_text(lines), reply_markup=kb.cart())


@router.callback_query(kb.CartCb.filter(F.action == "clear"))
async def clear_cart(call: CallbackQuery, db: Database) -> None:
    await db.clear_cart(call.from_user.id)
    await call.message.edit_text(texts.CART_CLEARED)
    await call.answer()


@router.callback_query(kb.CartCb.filter(F.action == "checkout"))
async def checkout(call: CallbackQuery, bot: Bot, db: Database, settings: Settings) -> None:
    order = await db.create_order(call.from_user.id, call.from_user.username)
    if order is None:
        await call.answer(texts.CART_EMPTY, show_alert=True)
        return
    await call.message.edit_text(
        texts.ORDER_PLACED.format(order_id=order.id, total=texts.money(order.total_cents))
    )
    await call.answer()
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, texts.order_summary(order))
        except TelegramAPIError:
            logger.exception("Could not notify admin %s about order %s", admin_id, order.id)


# --- admin commands -------------------------------------------------------


@router.message(Command("add"))
async def admin_add_product(
    message: Message, command: CommandObject, db: Database, settings: Settings
) -> None:
    if message.from_user.id not in settings.admin_ids:
        await message.answer(texts.NO_ACCESS)
        return
    try:
        name, cents, description = parse_add_args(command.args)
    except ValueError:
        await message.answer(texts.ADD_USAGE)
        return
    product_id = await db.add_product(name, description, cents)
    await message.answer(f"Добавлено: #{product_id} {name} — {texts.money(cents)}")


@router.message(Command("orders"))
async def admin_orders(message: Message, db: Database, settings: Settings) -> None:
    if message.from_user.id not in settings.admin_ids:
        await message.answer(texts.NO_ACCESS)
        return
    orders = await db.list_orders(limit=10)
    if not orders:
        await message.answer(texts.NO_ORDERS)
        return
    await message.answer("\n\n".join(texts.order_summary(o) for o in orders))
