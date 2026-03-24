from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from string import punctuation
from typing import Any, cast

bot_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(bot_dir))

from config import Settings, load_settings
from services.llm_client import LLMClient, LLMClientError, decode_tool_arguments
from services.lms_client import (
    LMSClient,
    LMSClientError,
    extract_labs,
    resolve_lab_identifier,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

COMMAND_HELP = (
    "Available commands:\n"
    "/start - welcome message\n"
    "/help - list commands\n"
    "/health - check backend status\n"
    "/labs - list available labs\n"
    "/scores <lab> - show per-task pass rates"
)

SYSTEM_PROMPT = """
You are an LMS Telegram bot for a software engineering course.
Use tools whenever the user asks about labs, scores, learners, groups, completion,
submissions, analytics, or refreshing data. Prefer tool calls over guessing.
If the user asks a comparison question, chain multiple tool calls and then summarize.
If the user greets you, answer briefly and mention what the bot can do.
If the user is ambiguous, ask a short clarifying question.
Keep answers concise, factual, and grounded only in tool results.
""".strip()

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "List all labs and tasks from the LMS backend.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get enrolled learners and their groups.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution buckets for a specific lab identifier like lab-04.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier such as lab-04.",
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
            "description": "Get per-task average scores and attempt counts for a lab like lab-04.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier such as lab-04.",
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
            "description": "Get submissions per day for a lab like lab-04.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier such as lab-04.",
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
            "description": "Get per-group performance for a lab like lab-03.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier such as lab-03.",
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
            "description": "Get the top learners for a lab with an optional limit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier such as lab-04.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of learners to return.",
                        "default": 5,
                    },
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion percentage for a lab like lab-05.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier such as lab-05.",
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
            "description": "Refresh LMS data by running the ETL sync pipeline.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


@dataclass
class BotRuntime:
    settings: Settings
    lms_client: LMSClient
    llm_client: LLMClient

    def route(self, raw_text: str) -> str:
        text = raw_text.strip()
        if not text:
            return "Please enter a command or question. Try /help."
        if text.startswith("/"):
            return self._route_command(text)
        return self._route_natural_language(text)

    def _route_command(self, text: str) -> str:
        parts = text.split()
        command = parts[0].lower()
        argument = " ".join(parts[1:]) if len(parts) > 1 else ""

        if command == "/start":
            return self._handle_start()
        if command == "/help":
            return self._handle_help()
        if command == "/health":
            return self._handle_health()
        if command == "/labs":
            return self._handle_labs()
        if command == "/scores":
            return self._handle_scores(argument)
        return f"Unknown command: {command}. Use /help."

    def _route_natural_language(self, text: str) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]

        try:
            for _ in range(6):
                response = self.llm_client.chat(
                    messages, tools=TOOLS, tool_choice="auto"
                )
                if response.tool_calls:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.content,
                            "tool_calls": response.tool_calls,
                        }
                    )
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["function"]["name"]
                        arguments = decode_tool_arguments(
                            tool_call["function"].get("arguments", "{}")
                        )
                        print(
                            f"[tool] LLM called: {tool_name}({json.dumps(arguments, ensure_ascii=True)})",
                            file=sys.stderr,
                        )
                        result = self._call_tool(tool_name, arguments)
                        size_hint = _result_size(result)
                        print(
                            f"[tool] Result: {size_hint} records",
                            file=sys.stderr,
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "name": tool_name,
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )
                    print("[summary] Feeding tool results back to LLM", file=sys.stderr)
                    continue
                if response.content.strip():
                    return response.content.strip()
                break
        except (LLMClientError, LMSClientError, json.JSONDecodeError) as exc:
            logger.warning("Natural language routing fell back after error: %s", exc)
            return self._fallback_natural_language(text, error=str(exc))

        return self._fallback_natural_language(text, error="")

    def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "get_items":
            return self.lms_client.get_items()
        if tool_name == "get_learners":
            return self.lms_client.get_learners()
        if tool_name == "get_scores":
            return self.lms_client.get_scores(str(arguments["lab"]))
        if tool_name == "get_pass_rates":
            return self.lms_client.get_pass_rates(str(arguments["lab"]))
        if tool_name == "get_timeline":
            return self.lms_client.get_timeline(str(arguments["lab"]))
        if tool_name == "get_groups":
            return self.lms_client.get_groups(str(arguments["lab"]))
        if tool_name == "get_top_learners":
            return self.lms_client.get_top_learners(
                str(arguments["lab"]),
                int(arguments.get("limit", 5)),
            )
        if tool_name == "get_completion_rate":
            return self.lms_client.get_completion_rate(str(arguments["lab"]))
        if tool_name == "trigger_sync":
            return self.lms_client.trigger_sync()
        raise LLMClientError(f"Unknown tool call: {tool_name}")

    def _fallback_natural_language(self, text: str, *, error: str) -> str:
        normalized = _normalize(text)
        if not normalized:
            return "Please enter a command or question. Try /help."

        if normalized <= {"hi"} or normalized <= {"hello"}:
            return (
                "Hello. I can show backend health, available labs, scores, groups, and learners. "
                "Try /help or ask something like 'what labs are available?'."
            )

        try:
            if "learners" in normalized or "students" in normalized:
                learners = self.lms_client.get_learners()
                groups = sorted(
                    {
                        str(row.get("student_group", "unknown"))
                        for row in learners
                        if row.get("student_group")
                    }
                )
                return f"There are {len(learners)} enrolled learners." + (
                    f" Groups: {', '.join(groups[:8])}." if groups else ""
                )

            if "labs" in normalized:
                return self._handle_labs()

            lab_id = self._extract_lab_from_text(text)
            if lab_id and ("score" in normalized or "pass" in normalized):
                return self._handle_scores(lab_id)

            if lab_id and "group" in normalized:
                rows = self.lms_client.get_groups(lab_id)
                if not rows:
                    return f"No group data found for {lab_id}."
                best = max(rows, key=lambda row: float(row.get("avg_score", 0.0)))
                return (
                    f"Best group for {lab_id}: {best.get('group', 'unknown')} with "
                    f"{float(best.get('avg_score', 0.0)):.1f}% average score across "
                    f"{int(best.get('students', 0))} students."
                )

            if lab_id and "top" in normalized:
                rows = self.lms_client.get_top_learners(lab_id, 5)
                if not rows:
                    return f"No learner ranking data found for {lab_id}."
                lines = [f"Top learners for {lab_id}:"]
                for index, row in enumerate(rows, start=1):
                    lines.append(
                        f"{index}. learner {row.get('learner_id')}: "
                        f"{float(row.get('avg_score', 0.0)):.1f}% "
                        f"({int(row.get('attempts', 0))} attempts)"
                    )
                return "\n".join(lines)

            if {"lowest", "worst"} & normalized and {
                "pass",
                "rate",
                "results",
                "score",
            } & normalized:
                items = self.lms_client.get_items()
                lab_ids: list[str] = []
                for lab in extract_labs(items):
                    item_id = str(lab.get("id", "")).zfill(2)
                    lab_ids.append(f"lab-{item_id}")
                ranking: list[tuple[str, float]] = []
                for candidate_lab_id in lab_ids:
                    pass_rates = self.lms_client.get_pass_rates(candidate_lab_id)
                    if not pass_rates:
                        continue
                    average = sum(
                        float(row.get("avg_score", 0.0)) for row in pass_rates
                    ) / len(pass_rates)
                    ranking.append((candidate_lab_id, average))
                if not ranking:
                    return "I could not compute lab rankings because no pass-rate data is available."
                worst_lab, average = min(ranking, key=lambda item: item[1])
                return f"Based on backend data, {worst_lab} has the lowest average pass rate at {average:.1f}%."

        except LMSClientError as exc:
            return self._format_backend_error(exc)

        base_message = (
            "I could not confidently map that question yet. "
            "Try /help or ask about labs, scores, learners, groups, or completion."
        )
        if error:
            return f"{base_message}\n\nLLM fallback reason: {error}"
        return base_message

    def _extract_lab_from_text(self, text: str) -> str | None:
        items = self.lms_client.get_items()
        lab_id = resolve_lab_identifier(text.strip(), items)
        if lab_id:
            return lab_id

        words = text.lower().replace("-", " ").split()
        for index, word in enumerate(words):
            if word == "lab" and index + 1 < len(words):
                candidate = words[index + 1]
                if candidate.isdigit():
                    return f"lab-{candidate.zfill(2)}"
            if word.startswith("lab") and word[3:].isdigit():
                return f"lab-{word[3:].zfill(2)}"
        return None

    def _handle_start(self) -> str:
        return (
            "Welcome to the SE Toolkit LMS bot.\n\n"
            "I can check backend health, list labs, show pass rates, and answer plain-text questions.\n\n"
            f"{COMMAND_HELP}"
        )

    def _handle_help(self) -> str:
        return (
            f"{COMMAND_HELP}\n\n"
            "Natural language examples:\n"
            "- what labs are available?\n"
            "- show me scores for lab 4\n"
            "- how many students are enrolled?\n"
            "- which group is doing best in lab 3?"
        )

    def _handle_health(self) -> str:
        try:
            items = self.lms_client.get_items()
        except LMSClientError as exc:
            return self._format_backend_error(exc)
        return f"Backend is healthy. {len(items)} items available."

    def _handle_labs(self) -> str:
        try:
            items = self.lms_client.get_items()
        except LMSClientError as exc:
            return self._format_backend_error(exc)

        labs = extract_labs(items)
        if not labs:
            return "No labs found in backend data."

        lines = ["Available labs:"]
        for lab in labs:
            lines.append(f"- {lab.get('title', 'Untitled lab')}")
        return "\n".join(lines)

    def _handle_scores(self, raw_lab: str) -> str:
        if not raw_lab.strip():
            return "Usage: /scores <lab>, example: /scores lab-04"

        try:
            items = self.lms_client.get_items()
            lab = resolve_lab_identifier(raw_lab, items)
            if not lab:
                return (
                    f"Lab '{raw_lab}' was not found. Use /labs to see valid lab names."
                )
            rows = self.lms_client.get_pass_rates(lab)
        except LMSClientError as exc:
            return self._format_backend_error(exc)

        if not rows:
            return (
                f"No pass-rate data for {raw_lab}. "
                "Check the lab name and run ETL sync if needed."
            )

        lines = [f"Pass rates for {lab}:"]
        for row in rows:
            task_name = str(row.get("task", "Unknown task"))
            avg_score = float(row.get("avg_score", 0.0))
            attempts = int(row.get("attempts", 0))
            lines.append(f"- {task_name}: {avg_score:.1f}% ({attempts} attempts)")
        return "\n".join(lines)

    def _format_backend_error(self, exc: Exception) -> str:
        return (
            "Backend error: "
            f"{exc}. Check that backend is running and LMS_API_* settings are correct."
        )


def _normalize(text: str) -> set[str]:
    translation = str.maketrans({char: " " for char in punctuation})
    lowered = text.lower().translate(translation)
    return {token for token in lowered.split() if token}


def _result_size(result: Any) -> int:
    if isinstance(result, list):
        return len(cast(list[Any], result))
    if isinstance(result, dict):
        return len(cast(dict[str, Any], result))
    return 0


def build_runtime() -> BotRuntime:
    settings = load_settings()
    return BotRuntime(
        settings=settings,
        lms_client=LMSClient(settings.lms_api_base_url, settings.lms_api_key),
        llm_client=LLMClient(
            settings.llm_api_key,
            settings.llm_api_base_url,
            settings.llm_api_model,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="SE Toolkit Lab 7 Telegram bot")
    parser.add_argument(
        "--test", type=str, help='Run one command, e.g. --test "/health"'
    )
    args = parser.parse_args()

    runtime = build_runtime()

    if args.test is not None:
        print(runtime.route(args.test))
        return

    run_telegram_bot(runtime)


def run_telegram_bot(runtime: BotRuntime) -> None:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import (
        Application,
        CallbackQueryHandler,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )

    if not runtime.settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required for Telegram mode")

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Health", callback_data="cmd:/health"),
                InlineKeyboardButton("Labs", callback_data="cmd:/labs"),
            ],
            [
                InlineKeyboardButton(
                    "Scores Lab 04", callback_data="cmd:/scores lab-04"
                ),
                InlineKeyboardButton(
                    "Lowest Pass Rate",
                    callback_data="ask:which lab has the lowest pass rate",
                ),
            ],
        ]
    )

    async def answer_text(
        update: Update,
        text: str,
        *,
        include_keyboard: bool = False,
    ) -> None:
        reply_markup = keyboard if include_keyboard else None
        if update.message is not None:
            await update.message.reply_text(text, reply_markup=reply_markup)
            return
        if update.callback_query is not None:
            callback_message = update.callback_query.message
            if callback_message is not None:
                await cast(Any, callback_message).reply_text(
                    text, reply_markup=reply_markup
                )

    async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await answer_text(update, runtime.route("/start"), include_keyboard=True)

    async def on_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await answer_text(update, runtime.route("/help"), include_keyboard=True)

    async def on_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await answer_text(update, runtime.route("/health"))

    async def on_labs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await answer_text(update, runtime.route("/labs"))

    async def on_scores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        lab = " ".join(context.args) if context.args else ""
        command = "/scores" if not lab else f"/scores {lab}"
        await answer_text(update, runtime.route(command))

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message is None or not update.message.text:
            return
        await answer_text(update, runtime.route(update.message.text))

    async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.callback_query is None or not update.callback_query.data:
            return
        await update.callback_query.answer()
        data = update.callback_query.data
        if data.startswith("cmd:"):
            await answer_text(update, runtime.route(data[4:]))
            return
        if data.startswith("ask:"):
            await answer_text(update, runtime.route(data[4:]))
            return
        await answer_text(update, "Unknown button action. Use /help.")

    while True:
        try:
            application = (
                Application.builder().token(runtime.settings.bot_token).build()
            )
            application.add_handler(CommandHandler("start", on_start))
            application.add_handler(CommandHandler("help", on_help))
            application.add_handler(CommandHandler("health", on_health))
            application.add_handler(CommandHandler("labs", on_labs))
            application.add_handler(CommandHandler("scores", on_scores))
            application.add_handler(CallbackQueryHandler(on_callback))
            application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, on_text)
            )
            logger.info("Starting Telegram bot polling")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            return
        except Exception:
            logger.exception(
                "Telegram startup failed, retrying in %s seconds",
                runtime.settings.telegram_retry_delay_seconds,
            )
            time.sleep(runtime.settings.telegram_retry_delay_seconds)


if __name__ == "__main__":
    main()
