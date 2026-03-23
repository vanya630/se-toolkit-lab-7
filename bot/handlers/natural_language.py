"""Handler for natural language queries via intent routing."""

import sys
from config import load_config
from services.lms_client import LMSClient, LMSClientError
from services.llm_client import LLMClient


def handle_natural_language(user_message: str) -> str:
    """Handle natural language queries via LLM intent routing.

    Args:
        user_message: The user's message

    Returns:
        Response text
    """
    config = load_config()

    # Check if LLM is configured
    if not config.get("llm_api_key"):
        return (
            "⚠️ LLM is not configured. Please set LLM_API_KEY in your .env.bot.secret file.\n\n"
            "Once configured, I can answer questions like:\n"
            "• What labs are available?\n"
            "• Which lab has the lowest pass rate?\n"
            "• Show me the top 5 students in lab 4"
        )

    try:
        # Initialize clients
        lms_client = LMSClient(
            base_url=config["lms_api_base_url"],
            api_key=config["lms_api_key"]
        )
        llm_client = LLMClient(
            api_key=config["llm_api_key"],
            base_url=config["llm_api_base_url"],
            model=config["llm_api_model"]
        )

        # Debug callback for stderr (only in test mode)
        def debug_log(message: str):
            print(message, file=sys.stderr)

        # Route the intent
        response = llm_client.route_intent(
            user_message=user_message,
            lms_client=lms_client,
            debug_callback=debug_log
        )

        return response

    except LMSClientError as e:
        return f"⚠️ Backend error: {str(e)}"
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"
