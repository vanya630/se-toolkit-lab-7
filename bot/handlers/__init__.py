"""Command handlers for the Telegram bot.

Handlers are pure functions that take input and return text.
They don't know about Telegram - this makes them testable.
"""

from handlers.start import handle_start
from handlers.help import handle_help
from handlers.health import handle_health
from handlers.labs import handle_labs
from handlers.scores import handle_scores

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
]
