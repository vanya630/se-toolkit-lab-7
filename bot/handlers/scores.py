"""Handler for /scores command."""

from config import load_config
from services.lms_client import LMSClient, LMSConnectionError, LMSAPIError


def handle_scores(user_input: str = "") -> str:
    """Handle the /scores command.
    
    Shows scores for a specific lab.
    
    Args:
        user_input: Lab name or ID (e.g., "lab-04")
        
    Returns:
        Scores information for the specified lab
    """
    if not user_input.strip():
        return (
            "⚠️ Please specify a lab name.\n\n"
            "Usage: /scores lab-04\n"
            "Available labs: Use /labs to see all available labs"
        )
    
    lab_name = user_input.strip()
    
    config = load_config()
    client = LMSClient(
        base_url=config["lms_api_base_url"],
        api_key=config["lms_api_key"]
    )
    
    try:
        # First, try to find the lab
        lab = client.get_lab_by_title(lab_name)
        
        if not lab:
            # Try to get pass rates directly (maybe lab_name is the ID)
            pass_rates = client.get_pass_rates(lab_name)
            
            if not pass_rates:
                return (
                    f"⚠️ Lab '{lab_name}' not found.\n\n"
                    "Use /labs to see all available labs.\n"
                    "Example: /scores lab-04"
                )
        else:
            # Get pass rates using the lab ID or title
            lab_id = lab.get("id", lab_name)
            pass_rates = client.get_pass_rates(str(lab_id))
        
        if not pass_rates:
            return (
                f"📊 Scores for {lab_name}:\n\n"
                f"No pass rate data available yet.\n"
                "Make sure students have submitted this lab."
            )
        
        # Format pass rates
        lines = [f"📊 Pass rates for {lab_name}:\n"]
        
        for rate in pass_rates:
            # API returns: task, avg_score, attempts
            task_name = rate.get("task", rate.get("task_title", rate.get("task_name", "Unknown Task")))
            avg_score = rate.get("avg_score", rate.get("pass_rate", 0))
            attempts = rate.get("attempts", 0)
            
            # Format percentage
            percentage = f"{avg_score:.1f}%" if isinstance(avg_score, (int, float)) else str(avg_score)
            
            lines.append(f"- {task_name}: {percentage} ({attempts} attempts)")
        
        return "\n".join(lines)
        
    except LMSConnectionError as e:
        return f"⚠️ Backend error: {str(e)}"
    except LMSAPIError as e:
        return f"⚠️ API error: {str(e)}"
    except Exception as e:
        return f"⚠️ Unexpected error: {str(e)}"
