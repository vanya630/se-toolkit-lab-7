FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app/bot

COPY bot/pyproject.toml ./
RUN uv sync --no-dev

COPY bot/ ./

CMD ["uv", "run", "bot.py"]
