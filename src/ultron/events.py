"""Lightweight event bus for ULTRON runtime integrations."""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class RuntimeEvent:
    """An in-process runtime event."""

    event_id: str
    event_type: str
    correlation_id: str
    timestamp: str
    payload: dict[str, Any]


Subscriber = Callable[[RuntimeEvent], None]


class EventBus:
    """Publish events to registered subscribers."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)

    def subscribe(self, event_type: str, subscriber: Subscriber) -> None:
        self._subscribers[event_type].append(subscriber)

    def publish(
        self,
        event_type: str,
        correlation_id: str,
        payload: dict[str, Any] | None = None,
    ) -> RuntimeEvent:
        event = RuntimeEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload or {},
        )
        for subscriber in (*self._subscribers.get(event_type, []), *self._subscribers.get("*", [])):
            subscriber(event)
        return event
