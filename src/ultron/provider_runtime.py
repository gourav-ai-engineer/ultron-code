"""HTTP runtime adapters for provider-neutral ULTRON CODE snapshots."""

from collections.abc import Callable, Mapping
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .providers import ProviderHealth, ProviderKind, ProviderSnapshot, ProviderStatus

JsonObject = dict[str, Any]
JsonFetcher = Callable[[str, Mapping[str, str]], JsonObject]


class ProviderRequestError(RuntimeError):
    """Raised when a provider endpoint cannot be queried."""


def fetch_json(
    url: str,
    headers: Mapping[str, str],
    timeout: float = 10.0,
) -> JsonObject:
    """Fetch one JSON object using the standard library."""
    request = Request(url, headers=dict(headers), method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ProviderRequestError(f"Provider request failed: {exc}") from exc

    if not isinstance(payload, dict):
        raise ProviderRequestError("Provider response was not a JSON object.")
    return payload


@dataclass
class OpenAIResponseAdapter:
    """Read a single OpenAI Responses API response."""

    response_id: str
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    fetcher: JsonFetcher = fetch_json

    @property
    def provider(self) -> ProviderKind:
        return ProviderKind.CHATGPT

    def health_check(self) -> ProviderHealth:
        try:
            self._fetch()
        except ProviderRequestError as exc:
            return ProviderHealth(self.provider, ProviderStatus.UNAVAILABLE, str(exc))
        return ProviderHealth(
            self.provider,
            ProviderStatus.AVAILABLE,
            "OpenAI Responses API endpoint is reachable.",
        )

    def snapshot(self) -> ProviderSnapshot:
        payload = self._fetch()
        status = str(payload.get("status", "unknown")).lower()
        summary = self._summary(payload)
        progress = _progress_from_status(status)
        return ProviderSnapshot(
            provider=self.provider,
            session_id=self.response_id,
            summary=summary,
            progress=progress,
        )

    def _fetch(self) -> JsonObject:
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderRequestError("OPENAI_API_KEY is not configured.")
        url = f"{self.base_url.rstrip('/')}/responses/{self.response_id}"
        return self.fetcher(url, {"Authorization": f"Bearer {api_key}"})

    @staticmethod
    def _summary(payload: JsonObject) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()[:2000]
        status = str(payload.get("status", "unknown"))
        return f"OpenAI response status: {status}"


@dataclass
class AnthropicModelsAdapter:
    """Read-only Claude API availability adapter.

    Anthropic's Models API exposes API/model availability rather than consumer
    Claude UI conversation state, so this adapter deliberately does not claim
    to monitor a Claude.app session.
    """

    api_key: str | None = None
    base_url: str = "https://api.anthropic.com"
    fetcher: JsonFetcher = fetch_json

    @property
    def provider(self) -> ProviderKind:
        return ProviderKind.CLAUDE

    def health_check(self) -> ProviderHealth:
        try:
            self._fetch()
        except ProviderRequestError as exc:
            return ProviderHealth(self.provider, ProviderStatus.UNAVAILABLE, str(exc))
        return ProviderHealth(
            self.provider,
            ProviderStatus.AVAILABLE,
            "Anthropic Models API is reachable.",
        )

    def snapshot(self) -> ProviderSnapshot:
        payload = self._fetch()
        models = payload.get("data")
        count = len(models) if isinstance(models, list) else 0
        return ProviderSnapshot(
            provider=self.provider,
            session_id=None,
            summary=f"Anthropic API reachable; {count} models visible.",
            progress=None,
        )

    def _fetch(self) -> JsonObject:
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderRequestError("ANTHROPIC_API_KEY is not configured.")
        url = f"{self.base_url.rstrip('/')}/v1/models"
        return self.fetcher(
            url,
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )


@dataclass
class CursorCloudRunAdapter:
    """Read one Cursor Cloud Agent run through the public Cloud Agents API."""

    agent_id: str
    run_id: str
    api_key: str | None = None
    base_url: str = "https://api.cursor.com/v1"
    fetcher: JsonFetcher = fetch_json

    @property
    def provider(self) -> ProviderKind:
        return ProviderKind.CURSOR

    def health_check(self) -> ProviderHealth:
        try:
            self._fetch()
        except ProviderRequestError as exc:
            return ProviderHealth(self.provider, ProviderStatus.UNAVAILABLE, str(exc))
        return ProviderHealth(
            self.provider,
            ProviderStatus.AVAILABLE,
            "Cursor Cloud Agents run endpoint is reachable.",
        )

    def snapshot(self) -> ProviderSnapshot:
        payload = self._fetch()
        status = str(payload.get("status", "unknown")).upper()
        result = payload.get("result")
        summary = result.strip() if isinstance(result, str) and result.strip() else f"Cursor run status: {status}"
        return ProviderSnapshot(
            provider=self.provider,
            session_id=self.run_id,
            summary=summary[:2000],
            progress=_cursor_progress(status),
        )

    def _fetch(self) -> JsonObject:
        api_key = self.api_key or os.getenv("CURSOR_API_KEY")
        if not api_key:
            raise ProviderRequestError("CURSOR_API_KEY is not configured.")
        url = (
            f"{self.base_url.rstrip('/')}/agents/"
            f"{self.agent_id}/runs/{self.run_id}"
        )
        return self.fetcher(url, {"Authorization": f"Bearer {api_key}"})


def _progress_from_status(status: str) -> float | None:
    if status in {"completed", "complete"}:
        return 1.0
    if status in {"in_progress", "queued", "running"}:
        return 0.5
    if status in {"failed", "cancelled", "canceled"}:
        return 0.0
    return None


def _cursor_progress(status: str) -> float | None:
    if status in {"FINISHED", "COMPLETED"}:
        return 1.0
    if status in {"CREATING", "RUNNING"}:
        return 0.5
    if status in {"FAILED", "CANCELLED"}:
        return 0.0
    return None
