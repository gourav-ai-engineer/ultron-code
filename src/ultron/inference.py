"""Free/low-cost model inference adapters for ULTRON CODE."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

JsonObject = dict[str, Any]
JsonPoster = Callable[[str, Mapping[str, str], JsonObject], JsonObject]


class InferenceRequestError(RuntimeError):
    """Raised when a model provider request fails."""


def post_json(
    url: str,
    headers: Mapping[str, str],
    payload: JsonObject,
    timeout: float = 60.0,
) -> JsonObject:
    """POST one JSON object using the standard library."""
    request = Request(
        url,
        headers={**dict(headers), "Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise InferenceRequestError(f"Model request failed: {exc}") from exc

    if not isinstance(result, dict):
        raise InferenceRequestError("Model response was not a JSON object.")
    return result


@dataclass(frozen=True)
class InferenceResult:
    """Normalized model response."""

    provider: str
    model: str
    text: str


@dataclass
class GeminiInference:
    """Gemini API text generation using a free-tier-capable model."""

    model: str = "gemini-3.8-flash"
    api_key: str | None = None
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    poster: JsonPoster = post_json

    def generate(self, prompt: str) -> InferenceResult:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise InferenceRequestError("GEMINI_API_KEY is not configured.")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ]
        }

        last_error: InferenceRequestError | None = None
        models = _gemini_model_candidates(self.model)
        for model in models:
            url = f"{self.base_url.rstrip('/')}/models/{model}:generateContent"
            try:
                response = _generate_with_retry(
                    self.poster,
                    url,
                    {"x-goog-api-key": api_key},
                    payload,
                )
            except InferenceRequestError as exc:
                last_error = exc
                if not _is_retryable_error(exc):
                    raise
                continue

            text = _gemini_text(response)
            if text:
                return InferenceResult("gemini", model, text)

            last_error = InferenceRequestError("Gemini returned no text output.")

        raise last_error or InferenceRequestError("Gemini generation failed.")


@dataclass
class OpenRouterFreeInference:
    """OpenRouter inference using its free-model router by default."""

    model: str = "openrouter/free"
    api_key: str | None = None
    base_url: str = "https://openrouter.ai/api/v1"
    poster: JsonPoster = post_json

    def generate(self, prompt: str) -> InferenceResult:
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise InferenceRequestError("OPENROUTER_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        response = self.poster(
            url,
            {"Authorization": f"Bearer {api_key}"},
            payload,
        )

        text = _openrouter_text(response)
        if not text:
            raise InferenceRequestError("OpenRouter returned no text output.")
        return InferenceResult("openrouter", self.model, text)


@dataclass
class OllamaInference:
    """Local Ollama inference; no API key or cloud billing required."""

    model: str
    base_url: str = "http://127.0.0.1:11434/api"
    poster: JsonPoster = post_json

    def generate(self, prompt: str) -> InferenceResult:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        url = f"{self.base_url.rstrip('/')}/chat"
        response = self.poster(url, {}, payload)

        message = response.get("message")
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise InferenceRequestError("Ollama returned no text output.")
        return InferenceResult("ollama", self.model, text.strip())



def _generate_with_retry(
    poster: JsonPoster,
    url: str,
    headers: Mapping[str, str],
    payload: JsonObject,
    attempts: int = 3,
) -> JsonObject:
    """Retry transient provider failures with exponential backoff."""
    last_error: InferenceRequestError | None = None
    for attempt in range(attempts):
        try:
            return poster(url, headers, payload)
        except InferenceRequestError as exc:
            last_error = exc
            if not _is_retryable_error(exc) or attempt == attempts - 1:
                raise
            time.sleep(2**attempt)
    raise last_error or InferenceRequestError("Provider request failed.")


def _is_retryable_error(exc: InferenceRequestError) -> bool:
    message = str(exc)
    return any(code in message for code in ("408", "429", "500", "502", "503", "504"))


def _gemini_model_candidates(model: str) -> tuple[str, ...]:
    candidates = [model]
    if model == "gemini-3.8-flash":
        candidates.extend(("gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash"))
    return tuple(dict.fromkeys(candidates))

def _gemini_text(payload: JsonObject) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return ""
    parts: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        candidate_parts = content.get("parts")
        if not isinstance(candidate_parts, list):
            continue
        for part in candidate_parts:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n".join(parts).strip()


def _openrouter_text(payload: JsonObject) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list):
        return ""
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        text = message.get("content")
        if isinstance(text, str) and text.strip():
            return text.strip()
    return ""
