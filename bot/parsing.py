"""Pure helpers with no Telegram dependency, so they are easy to unit-test."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation


def parse_add_args(text: str | None) -> tuple[str, int, str]:
    """Parse '/add' arguments: 'Name | 12.50 | Description' -> (name, price_cents, description).

    Raises ValueError when the input is missing or invalid.
    """
    if not text:
        raise ValueError("empty arguments")
    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 2 or not parts[0]:
        raise ValueError("name and price are required")
    try:
        price = Decimal(parts[1].replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("price is not a number") from exc
    if not price.is_finite() or price <= 0:
        raise ValueError("price must be positive")
    cents = int((price * 100).to_integral_value())
    if cents <= 0:
        raise ValueError("price is too small")
    description = parts[2] if len(parts) > 2 else ""
    return parts[0], cents, description
