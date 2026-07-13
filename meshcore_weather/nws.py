"""National Weather Service alert parsing and filtering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from meshcore_weather.config import GatewayConfig


@dataclass
class Observation:
    """A normalized current weather observation."""

    temperature_f: float | None = None
    humidity_percent: float | None = None
    station_id: str | None = None
    observation_time: str | None = None


@dataclass
class Alert:
    """A normalized weather alert."""

    id: str
    event: str
    headline: str
    description: str
    instruction: str
    severity: str
    sent: str
    expires: str
    sender_name: str
    area_desc: str
    zones: list[str]


def fetch_active_alerts(url: str = "https://api.weather.gov/alerts/active") -> dict[str, Any]:
    """Fetch active NWS alerts from the public API."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def fetch_weather_observation(location: str | None = None) -> Observation | None:
    """Fetch current weather conditions for the provided location from the NWS API."""
    if not location:
        return None

    try:
        response = requests.get(
            "https://api.weather.gov/points/" + location,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        observation_url = payload.get("properties", {}).get("observationStations")
        if not observation_url:
            return None

        stations_response = requests.get(observation_url, timeout=10)
        stations_response.raise_for_status()
        stations_payload = stations_response.json()
        features = stations_payload.get("features", [])
        if not features:
            return None

        station_id = features[0].get("properties", {}).get("stationIdentifier")
        if not station_id:
            return None

        obs_response = requests.get(
            f"https://api.weather.gov/stations/{station_id}/observations/latest",
            timeout=10,
        )
        obs_response.raise_for_status()
        obs_payload = obs_response.json()
        properties = obs_payload.get("properties", {})
        temperature = properties.get("temperature", {}).get("value")
        humidity = properties.get("relativeHumidity", {}).get("value")

        return Observation(
            temperature_f=float(temperature) * 9 / 5 + 32 if temperature is not None else None,
            humidity_percent=float(humidity) if humidity is not None else None,
            station_id=str(station_id),
            observation_time=str(properties.get("timestamp", "")),
        )
    except Exception:
        return None


def build_alerts(payload: dict[str, Any]) -> list[Alert]:
    """Parse NWS GeoJSON features into Alert objects."""
    features = payload.get("features", [])
    alerts: list[Alert] = []

    for feature in features:
        properties = feature.get("properties", {})
        geocode = properties.get("geocode", {})
        zones = [
            value
            for key in ("UGC", "SAME")
            for value in geocode.get(key, [])
            if isinstance(value, str)
        ]

        alerts.append(
            Alert(
                id=str(feature.get("id", "")),
                event=str(properties.get("event", "")),
                headline=str(properties.get("headline", "")),
                description=str(properties.get("description", "")),
                instruction=str(properties.get("instruction", "")),
                severity=str(properties.get("severity", "")),
                sent=str(properties.get("sent", "")),
                expires=str(properties.get("expires", "")),
                sender_name=str(properties.get("senderName", "")),
                area_desc=str(properties.get("areaDesc", "")),
                zones=zones,
            )
        )

    return alerts


def filter_alerts(alerts: list[Alert], config: GatewayConfig) -> list[Alert]:
    """Filter alerts to the configured state, tracked locations, and alert types."""
    configured_zones = {
        str(location.get("nws_zone", "")).strip().upper()
        for location in config.tracked_locations
        if str(location.get("nws_zone", "")).strip()
    }

    filtered: list[Alert] = []
    for alert in alerts:
        if config.state and alert.zones:
            matching_zone = any(zone.upper() == config.state for zone in alert.zones)
            if not matching_zone and not configured_zones:
                continue
            if configured_zones and not set(alert.zones).intersection(configured_zones):
                continue

        if alert.event not in config.alert_types:
            continue

        filtered.append(alert)

    return filtered
