import pytest

from ultron.inference import (
    GeminiInference,
    InferenceRequestError,
    OllamaInference,
    OpenRouterFreeInference,
)


def test_gemini_inference_parses_text() -> None:
    def poster(url, headers, payload):
        assert url.endswith("/models/gemini-test:generateContent")
        assert headers["x-goog-api-key"] == "gemini-key"
        assert payload["contents"][0]["parts"][0]["text"] == "hello"
        return {
            "candidates": [
                {"content": {"parts": [{"text": "Gemini response"}]}}
            ]
        }

    result = GeminiInference(
        model="gemini-test",
        api_key="gemini-key",
        poster=poster,
    ).generate("hello")

    assert result.provider == "gemini"
    assert result.model == "gemini-test"
    assert result.text == "Gemini response"


def test_openrouter_free_inference_parses_text() -> None:
    def poster(url, headers, payload):
        assert url.endswith("/chat/completions")
        assert headers["Authorization"] == "Bearer router-key"
        assert payload["model"] == "openrouter/free"
        return {
            "choices": [
                {"message": {"content": "Free router response"}}
            ]
        }

    result = OpenRouterFreeInference(
        api_key="router-key",
        poster=poster,
    ).generate("hello")

    assert result.provider == "openrouter"
    assert result.model == "openrouter/free"
    assert result.text == "Free router response"


def test_ollama_inference_parses_text() -> None:
    def poster(url, headers, payload):
        assert url.endswith("/api/chat")
        assert headers == {}
        assert payload["model"] == "local-model"
        assert payload["stream"] is False
        return {"message": {"content": "Local response"}}

    result = OllamaInference(
        model="local-model",
        poster=poster,
    ).generate("hello")

    assert result.provider == "ollama"
    assert result.model == "local-model"
    assert result.text == "Local response"


def test_gemini_requires_key() -> None:
    with pytest.raises(InferenceRequestError, match="GEMINI_API_KEY"):
        GeminiInference(api_key="").generate("hello")


def test_openrouter_requires_key() -> None:
    with pytest.raises(InferenceRequestError, match="OPENROUTER_API_KEY"):
        OpenRouterFreeInference(api_key="").generate("hello")
