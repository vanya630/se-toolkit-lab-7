from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file() -> None:
    search_paths = [
        Path(__file__).resolve().parent / ".env.bot.secret",
        Path(__file__).resolve().parent.parent / ".env.bot.secret",
    ]
    for env_path in search_paths:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
        return


@dataclass(frozen=True)
class Settings:
    bot_token: str
    lms_api_base_url: str
    lms_api_key: str
    llm_api_key: str
    llm_api_base_url: str
    llm_api_model: str
    telegram_retry_delay_seconds: int


def load_settings() -> Settings:
    _load_env_file()
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        lms_api_base_url=os.getenv("LMS_API_BASE_URL", "http://localhost:42002"),
        lms_api_key=os.getenv("LMS_API_KEY", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_api_base_url=os.getenv("LLM_API_BASE_URL", "http://localhost:42005/v1"),
        llm_api_model=os.getenv("LLM_API_MODEL", "qwen/qwen3-coder-plus"),
        telegram_retry_delay_seconds=int(
            os.getenv("TELEGRAM_RETRY_DELAY_SECONDS", "15")
        ),
    )
