from ultron.events import EventBus


def test_event_bus_dispatches_specific_and_wildcard() -> None:
    bus = EventBus()
    seen: list[str] = []

    bus.subscribe("run.completed", lambda event: seen.append(event.event_type))
    bus.subscribe("*", lambda event: seen.append("all"))

    event = bus.publish("run.completed", "run-1", {"ok": True})

    assert event.correlation_id == "run-1"
    assert seen == ["run.completed", "all"]
