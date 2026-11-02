"""Settings are read from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    db_path: str


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Copy .env.example to .env and put your token there."
        )
    raw_ids = os.getenv("ADMIN_IDS", "").replace(" ", "")
    try:
        admin_ids = frozenset(int(x) for x in raw_ids.split(",") if x)
    except ValueError as exc:
        raise RuntimeError("ADMIN_IDS must be a comma-separated list of numbers") from exc
    return Settings(
        bot_token=token,
        admin_ids=admin_ids,
        db_path=os.getenv("DB_PATH", "shop.db"),
    )
