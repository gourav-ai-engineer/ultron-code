"""Provider registry and factory selection for ULTRON CODE."""

from collections.abc import Callable
from typing import Any

from .provider_runtime import AnthropicModelsAdapter, CursorCloudRunAdapter, OpenAIResponseAdapter
from .providers import MockProvider, ProviderAdapter, ProviderKind

ProviderFactory = Callable[..., ProviderAdapter]


class ProviderRegistry:
    """Resolve provider names into configured read-only adapters."""

    def __init__(self) -> None:
        self._factories: dict[ProviderKind, ProviderFactory] = {
            ProviderKind.CHATGPT: OpenAIResponseAdapter,
            ProviderKind.CLAUDE: AnthropicModelsAdapter,
            ProviderKind.CURSOR: CursorCloudRunAdapter,
            ProviderKind.MOCK: MockProvider,
        }

    def register(self, kind: ProviderKind | str, factory: ProviderFactory) -> None:
        """Register or replace a provider adapter factory."""
        self._factories[ProviderKind(kind)] = factory

    def create(self, kind: ProviderKind | str, **kwargs: Any) -> ProviderAdapter:
        """Create one provider adapter from its registered factory."""
        provider = ProviderKind(kind)
        try:
            factory = self._factories[provider]
        except KeyError as exc:
            raise ValueError(f"Provider is not registered: {provider.value}") from exc
        try:
            return factory(**kwargs)
        except TypeError as exc:
            raise ValueError(
                f"Invalid configuration for provider '{provider.value}': {exc}"
            ) from exc

    def available(self) -> tuple[ProviderKind, ...]:
        """Return registered provider kinds in deterministic order."""
        return tuple(self._factories)
