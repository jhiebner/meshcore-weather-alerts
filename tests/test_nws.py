from meshcore_weather.config import GatewayConfig
from meshcore_weather.nws import Alert, build_alerts, filter_alerts


SAMPLE_ALERTS = {
    "features": [
        {
            "id": "abc123",
            "properties": {
                "event": "Tornado Warning",
                "headline": "Tornado Warning for York County",
                "description": "Take shelter immediately.",
                "instruction": "Move to a basement or interior room.",
                "severity": "Severe",
                "sent": "2026-07-13T01:00:00+00:00",
                "expires": "2026-07-13T02:00:00+00:00",
                "senderName": "NWS Omaha/Valley",
                "areaDesc": "York County, Nebraska",
                "geocode": {"UGC": ["NEC185"], "SAME": ["NEC185"]},
            },
        },
        {
            "id": "def456",
            "properties": {
                "event": "Flood Warning",
                "headline": "Flood Warning for Hamilton County",
                "description": "Water rising.",
                "instruction": "Avoid flooded roads.",
                "severity": "Moderate",
                "sent": "2026-07-13T01:10:00+00:00",
                "expires": "2026-07-13T02:10:00+00:00",
                "senderName": "NWS Omaha/Valley",
                "areaDesc": "Hamilton County, Nebraska",
                "geocode": {"UGC": ["NEC081"], "SAME": ["NEC081"]},
            },
        },
    ]
}


def test_build_alerts_parses_sample_payload() -> None:
    alerts = build_alerts(SAMPLE_ALERTS)

    assert len(alerts) == 2
    assert alerts[0].event == "Tornado Warning"
    assert alerts[0].headline == "Tornado Warning for York County"


def test_filter_alerts_matches_configured_county_and_alert_type() -> None:
    config = GatewayConfig(
        serial_port="/dev/ttyUSB0",
        state="NE",
        tracked_locations=[{"county": "York", "nws_zone": "NEC185"}],
        alert_types=["Tornado Warning"],
        poll_interval_seconds=60,
        repeat_interval_minutes=15,
    )

    alerts = build_alerts(SAMPLE_ALERTS)
    filtered = filter_alerts(alerts, config)

    assert len(filtered) == 1
    assert filtered[0].id == "abc123"
    assert isinstance(filtered[0], Alert)
