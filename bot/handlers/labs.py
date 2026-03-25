"""Handler for /labs command."""

from config import load_config
from services.lms_client import LMSClient, LMSConnectionError, LMSAPIError


def handle_labs(user_input: str = "") -> str:
    """Handle the /labs command.

    Lists all available labs.

    Args:
        user_input: Optional input from user (not used for /labs)

    Returns:
        List of available labs
    """
    config = load_config()
    client = LMSClient(
        base_url=config["lms_api_base_url"],
        api_key=config["lms_api_key"]
    )

    try:
        labs = client.get_labs()

        if not labs:
            return (
                "📋 No labs found.\n\n"
                "The backend may not have any labs yet, or the ETL sync hasn't run.\n"
                "Run: curl -X POST http://localhost:42002/pipeline/sync -H 'Authorization: Bearer YOUR_KEY' -d '{}'"
            )

        lab_list = []
        for lab in labs:
            lab_id = lab.get("id", "?")
            lab_title = lab.get("title", "Unknown Lab")

            # Format: "- Lab 01 — Products, Architecture & Roles"
            # Extract lab number and title from the title field
            lab_list.append(f"- {lab_title}")

        return (
            "Available labs:\n"
            + "\n".join(lab_list)
        )

    except LMSConnectionError as e:
        return f"Backend error: {str(e)}"
    except LMSAPIError as e:
        return f"Backend error: {str(e)}"
    except Exception as e:
        return f"Backend error: {str(e)}"
