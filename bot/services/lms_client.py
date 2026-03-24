from __future__ import annotations

from urllib.parse import urlparse
from typing import Any, cast

import httpx


class LMSClientError(RuntimeError):
    pass


class LMSClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 12.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise LMSClientError("LMS_API_KEY is empty in .env.bot.secret")
        return {"Authorization": f"Bearer {self.api_key}"}

    def _host_label(self) -> str:
        parsed = urlparse(self.base_url)
        return parsed.netloc or self.base_url

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method,
                    url,
                    headers=self._headers(),
                    params=params,
                    json=json,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            reason = exc.response.reason_phrase
            raise LMSClientError(f"HTTP {status} {reason}.") from exc
        except httpx.ConnectError as exc:
            raise LMSClientError(
                f"connection refused ({self._host_label()}). Backend service may be down."
            ) from exc
        except httpx.TimeoutException as exc:
            raise LMSClientError(
                f"request timeout while contacting {self._host_label()}."
            ) from exc
        except httpx.HTTPError as exc:
            raise LMSClientError(str(exc)) from exc

    def get_items(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/items/")
        if isinstance(payload, list):
            return cast(list[dict[str, Any]], payload)
        raise LMSClientError("Unexpected response from /items/")

    def get_learners(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/learners/")
        if isinstance(payload, list):
            return cast(list[dict[str, Any]], payload)
        raise LMSClientError("Unexpected response from /learners/")

    def get_scores(self, lab: str) -> list[dict[str, Any]]:
        payload = self._request("GET", "/analytics/scores", params={"lab": lab})
        if isinstance(payload, list):
            return cast(list[dict[str, Any]], payload)
        raise LMSClientError("Unexpected response from /analytics/scores")

    def get_pass_rates(self, lab: str) -> list[dict[str, Any]]:
        payload = self._request("GET", "/analytics/pass-rates", params={"lab": lab})
        if isinstance(payload, list):
            return cast(list[dict[str, Any]], payload)
        raise LMSClientError("Unexpected response from /analytics/pass-rates")

    def get_timeline(self, lab: str) -> list[dict[str, Any]]:
        payload = self._request("GET", "/analytics/timeline", params={"lab": lab})
        if isinstance(payload, list):
            return cast(list[dict[str, Any]], payload)
        raise LMSClientError("Unexpected response from /analytics/timeline")

    def get_groups(self, lab: str) -> list[dict[str, Any]]:
        payload = self._request("GET", "/analytics/groups", params={"lab": lab})
        if isinstance(payload, list):
            return cast(list[dict[str, Any]], payload)
        raise LMSClientError("Unexpected response from /analytics/groups")

    def get_top_learners(self, lab: str, limit: int = 5) -> list[dict[str, Any]]:
        payload = self._request(
            "GET",
            "/analytics/top-learners",
            params={"lab": lab, "limit": limit},
        )
        if isinstance(payload, list):
            return cast(list[dict[str, Any]], payload)
        raise LMSClientError("Unexpected response from /analytics/top-learners")

    def get_completion_rate(self, lab: str) -> dict[str, Any]:
        payload = self._request(
            "GET", "/analytics/completion-rate", params={"lab": lab}
        )
        if isinstance(payload, dict):
            return cast(dict[str, Any], payload)
        raise LMSClientError("Unexpected response from /analytics/completion-rate")

    def trigger_sync(self) -> dict[str, Any]:
        payload = self._request("POST", "/pipeline/sync", json={})
        if isinstance(payload, dict):
            return cast(dict[str, Any], payload)
        raise LMSClientError("Unexpected response from /pipeline/sync")


def extract_labs(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if str(item.get("type", "")).lower() == "lab"]


def resolve_lab_identifier(
    requested_lab: str,
    items: list[dict[str, Any]],
) -> str | None:
    candidate = requested_lab.strip().lower()
    if not candidate:
        return None

    labs = extract_labs(items)
    for lab in labs:
        title = str(lab.get("title", ""))
        lowered = title.lower()
        item_id = str(lab.get("id", "")).strip()
        if candidate == item_id:
            return f"lab-{item_id.zfill(2)}"
        if candidate == f"lab-{item_id.zfill(2)}":
            return candidate
        if candidate == title.lower():
            return f"lab-{item_id.zfill(2)}"
        if candidate in lowered:
            return f"lab-{item_id.zfill(2)}"
        compact_title = lowered.replace(" ", "")
        if candidate.replace(" ", "") == compact_title:
            return f"lab-{item_id.zfill(2)}"
    return candidate if candidate.startswith("lab-") else None
