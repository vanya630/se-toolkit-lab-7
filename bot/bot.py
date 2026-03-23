"""SE Toolkit Lab 7 - Telegram Bot Entry Point.

Usage:
    uv run bot.py              # Start Telegram bot
    uv run bot.py --test CMD   # Test mode (no Telegram connection)
"""

import sys
import argparse
import logging
from pathlib import Path

# Add bot directory to path for imports
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

from config import load_config

# Import handlers directly to avoid circular imports
from handlers.start import handle_start
from handlers.help import handle_help
from handlers.health import handle_health
from handlers.labs import handle_labs
from handlers.scores import handle_scores

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Command routing for test mode
COMMANDS = {
    "/start": handle_start,
    "/help": handle_help,
    "/health": handle_health,
    "/labs": handle_labs,
    "/scores": handle_scores,
}


def get_handler_for_command(command: str):
    """Get the appropriate handler for a command.
    
    Args:
        command: Command string (e.g., "/start" or "/scores lab-04")
        
    Returns:
        Tuple of (handler_function, user_input)
    """
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    user_input = parts[1] if len(parts) > 1 else ""
    
    handler = COMMANDS.get(cmd)
    if handler:
        return handler, user_input
    
    # Unknown command - return help handler
    return handle_help, ""


def run_test_mode(command: str) -> int:
    """Run the bot in test mode.
    
    Calls handlers directly without Telegram connection.
    Prints response to stdout and exits.
    
    Args:
        command: Command to test (e.g., "/start" or "what labs are available")
        
    Returns:
        Exit code (0 for success)
    """
    config = load_config()
    logger.info(f"Test mode: {command}")
    logger.info(f"Config loaded: LMS API = {config['lms_api_base_url']}")
    
    handler, user_input = get_handler_for_command(command)
    response = handler(user_input)
    
    print(response)
    return 0


def run_telegram_bot():
    """Run the Telegram bot.
    
    Connects to Telegram and starts listening for messages.
    """
    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            filters,
            ContextTypes,
        )
    except ImportError:
        logger.error("Telegram bot library not installed. Run: uv sync")
        sys.exit(1)
    
    config = load_config()
    
    if not config["bot_token"]:
        logger.error("BOT_TOKEN not configured. Check .env.bot.secret")
        sys.exit(1)

    logger.info("Starting Telegram bot...")
    logger.info(f"LMS API: {config['lms_api_base_url']}")
    logger.info(f"LLM API: {config['llm_api_base_url']}")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle natural language messages (for Task 3 - intent routing)."""
        user_message = update.message.text

        # TODO: Implement intent routing in Task 3
        # For now, respond with a placeholder
        response = (
            "🤔 I received your message. Intent routing will be implemented in Task 3.\n\n"
            f"You said: {user_message}\n\n"
            "Try commands like /start, /help, /labs, or /scores lab-04"
        )
        
        await update.message.reply_text(response)
    
    # Create application
    application = Application.builder().token(config["bot_token"]).build()

    # Add a single command handler for all commands
    # We use a MessageHandler with a filter to catch all commands
    async def handle_all_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all Telegram commands."""
        # Get the full command text (e.g., "/scores lab-04")
        full_text = update.message.text or ""
        
        # Get any arguments after the command
        parts = full_text.split(maxsplit=1)
        user_input = parts[1] if len(parts) > 1 else ""

        # Route to appropriate handler based on command
        handler, _ = get_handler_for_command(parts[0])
        response = handler(user_input)

        await update.message.reply_text(response)

    application.add_handler(MessageHandler(filters.COMMAND, handle_all_commands))

    # Add message handler for natural language
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SE Toolkit Lab 7 - Telegram Bot"
    )
    parser.add_argument(
        "--test",
        metavar="CMD",
        help="Test mode: run a command without Telegram connection",
    )
    
    args = parser.parse_args()
    
    if args.test:
        sys.exit(run_test_mode(args.test))
    
    run_telegram_bot()


if __name__ == "__main__":
    main()
