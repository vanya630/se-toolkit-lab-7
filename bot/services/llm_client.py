"""LLM client for intent routing and natural language queries with tool calling."""

import json
import httpx


# Maximum number of tool call iterations
MAX_TOOL_CALLS = 10

# System prompt for intent routing
SYSTEM_PROMPT = """You are an intelligent assistant for a Software Engineering course.
You help students understand their progress, lab results, and course analytics.

You have access to 9 tools that query the backend API. Use these tools to answer questions:

1. **get_items**: List all labs and tasks. Use for "what labs are available", "list labs", "show tasks".
2. **get_learners**: Get enrolled students and groups. Use for "how many students", "list learners", "enrollment".
3. **get_scores**: Get score distribution (4 buckets: 0-25, 26-50, 51-75, 76-100) for a lab. Use for "score distribution", "how are scores spread".
4. **get_pass_rates**: Get per-task average scores and attempt counts for a lab. Use for "pass rates", "task performance", "average scores".
5. **get_timeline**: Get submissions per day for a lab. Use for "submission timeline", "when did students submit", "activity over time".
6. **get_groups**: Get per-group scores and student counts for a lab. Use for "group comparison", "which group is best", "group performance".
7. **get_top_learners**: Get top N learners by score for a lab. Use for "top students", "leaderboard", "best performers".
8. **get_completion_rate**: Get completion rate percentage for a lab. Use for "completion rate", "how many passed", "pass percentage".
9. **trigger_sync**: Refresh data from autochecker. Use when user asks to "refresh", "sync", or "update data".

Rules:
- ALWAYS use tools to get real data before answering questions about labs, scores, or students.
- For comparison questions (e.g., "which lab has the lowest"), call tools for each item and compare.
- If a user asks about a specific lab, use the lab identifier (e.g., "lab-01", "lab-04").
- If the user's message is a greeting, respond warmly without using tools.
- If the user's message is unclear or gibberish, politely ask for clarification and suggest what you can help with.
- After calling tools, use the results to provide a concise, helpful answer with specific numbers.
- Format your answers clearly with bullet points or numbered lists when appropriate.

When you need data, call the appropriate tool(s). After receiving tool results, summarize the findings for the user.
"""

# Tool definitions for LLM function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "List all labs and tasks in the system. Use for questions about what labs are available or to get lab identifiers.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get all enrolled learners and their groups. Use for questions about student enrollment, how many students, or group membership.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution (4 buckets: 0-25, 26-50, 51-75, 76-100) for a specific lab. Use for questions about score distribution or how students performed overall.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'"
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a specific lab. Use for questions about task performance, pass rates, or average scores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'"
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submissions per day for a specific lab. Use for questions about submission timeline, when students submitted, or activity over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'"
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group average scores and student counts for a specific lab. Use for comparing groups or finding which group performed best/worst.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'"
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by average score for a specific lab. Use for leaderboard questions, top students, or best performers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top learners to return (default: 10)"
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate percentage for a specific lab. Use for questions about pass percentage, how many students completed, or completion statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'"
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger a data sync from the autochecker to refresh the latest submissions. Use when user asks to refresh, sync, or update data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


class LLMClient:
    """Client for the LLM API (Qwen Code) with tool calling support."""

    def __init__(self, api_key: str, base_url: str, model: str):
        """Initialize the LLM client.

        Args:
            api_key: API key for authentication
            base_url: Base URL of the LLM API
            model: Model name to use
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        )

    def chat(self, messages: list[dict]) -> str:
        """Send a chat completion request (no tools).

        Args:
            messages: List of message dicts with role and content

        Returns:
            Response text from the LLM
        """
        try:
            response = self._client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.RequestError as e:
            return f"LLM error: {e}"

    def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        timeout: int = 60
    ) -> dict:
        """Send a chat completion request with tool definitions.

        Args:
            messages: List of message dicts with role and content
            tools: List of tool definitions (default: TOOLS)
            timeout: Request timeout in seconds

        Returns:
            Parsed response dict with message and optional tool_calls
        """
        if tools is None:
            tools = TOOLS

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.7,
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data
        except httpx.TimeoutException:
            return {
                "error": f"LLM API timeout after {timeout} seconds"
            }
        except httpx.HTTPStatusError as e:
            return {
                "error": f"LLM API returned status {e.response.status_code}: {e.response.text}"
            }
        except httpx.RequestError as e:
            return {
                "error": f"Failed to connect to LLM API: {e}"
            }

    def detect_intent(self, user_message: str) -> str:
        """Detect the intent of a user message.

        Args:
            user_message: The user's message

        Returns:
            Intent name (e.g., "start", "help", "health", "labs", "scores")
        """
        system_prompt = (
            "You are an intent classifier for a Telegram bot. "
            "Classify the user message into one of these intents: "
            "start, help, health, labs, scores, or general. "
            "Respond with ONLY the intent name."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = self.chat(messages)
        return response.strip().lower()

    def route_intent(
        self,
        user_message: str,
        lms_client,
        debug_callback=None
    ) -> str:
        """Route a user message through the LLM tool-calling loop.

        Args:
            user_message: The user's message
            lms_client: LMSClient instance for executing tools
            debug_callback: Optional callback for debug logging

        Returns:
            Final response text
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        tool_calls_log = []

        for iteration in range(MAX_TOOL_CALLS):
            # Call LLM with tools
            response = self.chat_with_tools(messages)

            if "error" in response:
                return f"⚠️ LLM error: {response['error']}"

            # Get the assistant message
            assistant_message = response["choices"][0]["message"]

            # Check for tool calls
            tool_calls = assistant_message.get("tool_calls", [])

            if tool_calls:
                # Execute each tool call
                for tool_call in tool_calls:
                    # Extract tool info
                    function_info = tool_call.get("function", {})
                    tool_name = function_info.get("name", "")
                    tool_args_str = function_info.get("arguments", "{}")

                    try:
                        tool_args = json.loads(tool_args_str) if tool_args_str else {}
                    except json.JSONDecodeError:
                        tool_args = {}

                    # Execute the tool
                    result = self._execute_tool(tool_name, tool_args, lms_client)

                    # Debug logging
                    if debug_callback:
                        debug_callback(f"[tool] LLM called: {tool_name}({tool_args})")
                        debug_callback(f"[tool] Result: {self._summarize_result(result)}")

                    tool_calls_log.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result,
                    })

                    # Append tool result to messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", str(len(tool_calls_log))),
                        "content": json.dumps(result) if not isinstance(result, str) else result,
                    })

                # Continue loop to get next LLM response
                if debug_callback:
                    debug_callback(f"[summary] Feeding {len(tool_calls_log)} tool result(s) back to LLM")
                continue

            else:
                # No tool calls - this is the final answer
                return assistant_message.get("content", "I'm not sure how to help with that.")

        # Max iterations reached
        return "I reached the maximum number of tool calls. Based on the information gathered, I cannot provide a complete answer."

    def _execute_tool(self, name: str, args: dict, lms_client) -> dict | list | str:
        """Execute a tool by name with given arguments.

        Args:
            name: Tool name
            args: Tool arguments dict
            lms_client: LMSClient instance

        Returns:
            Tool result
        """
        try:
            if name == "get_items":
                return lms_client.get_items()
            elif name == "get_learners":
                return lms_client.get_learners()
            elif name == "get_scores":
                return lms_client.get_scores(args.get("lab", ""))
            elif name == "get_pass_rates":
                return lms_client.get_pass_rates(args.get("lab", ""))
            elif name == "get_timeline":
                return lms_client.get_timeline(args.get("lab", ""))
            elif name == "get_groups":
                return lms_client.get_groups(args.get("lab", ""))
            elif name == "get_top_learners":
                return lms_client.get_top_learners(
                    args.get("lab", ""),
                    args.get("limit", 10)
                )
            elif name == "get_completion_rate":
                return lms_client.get_completion_rate(args.get("lab", ""))
            elif name == "trigger_sync":
                return lms_client.trigger_sync()
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": str(e)}

    def _summarize_result(self, result) -> str:
        """Create a short summary of a tool result for debugging."""
        if isinstance(result, list):
            return f"{len(result)} items"
        elif isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            return f"Dict with {len(result)} keys"
        else:
            return str(result)[:100]
