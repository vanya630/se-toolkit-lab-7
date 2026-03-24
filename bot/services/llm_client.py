from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

import httpx


@dataclass(frozen=True)
class LLMResponse:
    content: str
    tool_calls: list[dict[str, Any]]


class LLMClientError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMClientError("LLM_API_KEY is empty in .env.bot.secret")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice

        try:
            with httpx.Client(timeout=45.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            reason = exc.response.reason_phrase
            raise LLMClientError(
                f"HTTP {exc.response.status_code} {reason} from LLM API."
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMClientError("LLM request timed out.") from exc
        except httpx.HTTPError as exc:
            raise LLMClientError(str(exc)) from exc

        data = response.json()
        message = data["choices"][0]["message"]
        raw_tool_calls: Any = message.get("tool_calls") or []
        tool_calls = cast(list[dict[str, Any]], raw_tool_calls)
        return LLMResponse(
            content=cast(str, message.get("content") or ""),
            tool_calls=tool_calls,
        )


def decode_tool_arguments(arguments: str) -> dict[str, Any]:
    if not arguments.strip():
        return {}
    return json.loads(arguments)
