from meshcore_weather.dedupe import AlertTracker


def test_alert_tracker_prevents_duplicate_alerts() -> None:
    tracker = AlertTracker()

    assert tracker.should_broadcast("abc123") is True
    assert tracker.should_broadcast("abc123") is False
    assert tracker.should_broadcast("def456") is True
