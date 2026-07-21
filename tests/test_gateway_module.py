from meshcore_weather.dedupe import AlertTracker
from meshcore_weather.gateway import run_gateway, run_test_mode


def test_gateway_module_exposes_runtime_handlers() -> None:
    assert callable(run_gateway)
    assert callable(run_test_mode)


def test_alert_tracker_disables_repeat_when_interval_is_zero() -> None:
    tracker = AlertTracker()

    assert tracker.should_broadcast("alert-1", repeat_interval_minutes=0)
    assert not tracker.should_broadcast("alert-1", repeat_interval_minutes=0)


def test_alert_tracker_allows_repeat_after_interval_elapsed() -> None:
    tracker = AlertTracker()

    assert tracker.should_broadcast("alert-2", repeat_interval_minutes=5, now=0)
    assert not tracker.should_broadcast("alert-2", repeat_interval_minutes=5, now=100)
    assert tracker.should_broadcast("alert-2", repeat_interval_minutes=5, now=301)
