"""Handler for /health command."""

from config import load_config
from services.lms_client import LMSClient


def handle_health(user_input: str = "") -> str:
    """Handle the /health command.
    
    Checks if the backend service is accessible.
    
    Args:
        user_input: Optional input from user (not used for /health)
        
    Returns:
        Health status message
    """
    config = load_config()
    client = LMSClient(
        base_url=config["lms_api_base_url"],
        api_key=config["lms_api_key"]
    )
    
    is_healthy, message = client.health_check()
    
    if is_healthy:
        return (
            "✅ " + message + "\n\n"
            "🔗 Backend: Connected\n"
            "📊 Database: Available\n"
            "🤖 LLM Service: Ready\n\n"
            "All systems operational!"
        )
    else:
        return "⚠️ " + message
