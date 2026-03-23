"""Handler for /start command."""

from typing import Any


def handle_start(user_input: str = "") -> str:
    """Handle the /start command.

    Args:
        user_input: Optional input from user (not used for /start)

    Returns:
        Welcome message text
    """
    return (
        "👋 Welcome to the SE Toolkit Lab 7 Bot!\n\n"
        "I'm your assistant for tracking lab progress and scores.\n\n"
        "Available commands:\n"
        "/start - Show this welcome message\n"
        "/help - Show available commands\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - Get scores for a specific lab\n\n"
        "You can also ask me questions like:\n"
        "• What labs are available?\n"
        "• Show scores for lab-04\n"
        "• Which lab has the lowest pass rate?\n"
        "• Who are the top 5 students?"
    )


def get_start_keyboard() -> list[list[dict[str, Any]]]:
    """Get inline keyboard buttons for /start command.

    Returns:
        Inline keyboard markup for Telegram
    """
    return [
        [
            {"text": "📋 Available Labs", "callback_data": "cmd_labs"},
            {"text": "💊 Health Check", "callback_data": "cmd_health"},
        ],
        [
            {"text": "❓ Help", "callback_data": "cmd_help"},
            {"text": "📊 Scores (lab-04)", "callback_data": "cmd_scores_lab-04"},
        ],
        [
            {"text": "🏆 Top Students", "callback_data": "query_top_students"},
            {"text": "📈 Lowest Pass Rate", "callback_data": "query_lowest_pass"},
        ],
    ]
