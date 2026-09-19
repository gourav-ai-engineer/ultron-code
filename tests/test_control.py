from ultron.control import ControlStore


def test_control_store_round_trip(tmp_path) -> None:
    store = ControlStore(tmp_path / "control.json")

    state = store.set(emergency_stop=True, reason="Operator requested stop.")

    assert state.emergency_stop is True
    assert store.get().reason == "Operator requested stop."
