"""National Weather Service alert parsing and filtering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from meshcore_weather.config import GatewayConfig


@dataclass
class ForecastPeriod:
    """A normalized forecast period."""

    name: str
    short_forecast: str
    detailed_forecast: str
    temperature: int | None = None
    temperature_unit: str | None = None


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


def fetch_forecast(location: str | None = None) -> list[ForecastPeriod]:
    """Fetch the next forecast periods for the provided coordinates from the NWS API."""
    if not location:
        return []

    try:
        response = requests.get(
            "https://api.weather.gov/points/" + location,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        forecast_url = payload.get("properties", {}).get("forecast")
        if not forecast_url:
            return []

        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_response.raise_for_status()
        forecast_payload = forecast_response.json()
        periods = forecast_payload.get("properties", {}).get("periods", [])
        return [
            ForecastPeriod(
                name=str(period.get("name", "")),
                short_forecast=str(period.get("shortForecast", "")),
                detailed_forecast=str(period.get("detailedForecast", "")),
                temperature=int(period.get("temperature")) if period.get("temperature") is not None else None,
                temperature_unit=str(period.get("temperatureUnit", "")),
            )
            for period in periods
        ]
    except Exception:
        return []


def fetch_location_zones(location: str | None = None) -> set[str]:
    """Fetch the NWS forecast/county zones for the provided coordinates."""
    if not location:
        return set()

    try:
        response = requests.get(
            "https://api.weather.gov/points/" + location,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        properties = payload.get("properties", {})
        zones: set[str] = set()

        for key in ("forecastZone", "county", "fireWeatherZone"):
            value = properties.get(key)
            if isinstance(value, str):
                zones.add(value.rsplit("/", 1)[-1])
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        zones.add(item.rsplit("/", 1)[-1])

        return zones
    except Exception:
        return set()


def _period_value(period: Any, *keys: str, default: Any = None) -> Any:
    """Read a value from a forecast period using one of several supported field names."""
    if isinstance(period, dict):
        for key in keys:
            if key in period:
                return period[key]
        return default

    for key in keys:
        value = getattr(period, key, None)
        if value is not None:
            return value

    return default


def build_forecast_message(payload: dict[str, Any]) -> str:
    """Build a compact message with the first forecast period for the day."""
    periods = payload.get("properties", {}).get("periods", [])
    if not periods:
        return "Forecast unavailable"

    period = periods[0]
    temperature = _period_value(period, "temperature")
    temperature_unit = _period_value(period, "temperatureUnit", "temperature_unit", default="F")
    name = _period_value(period, "name", default="Today")
    short_forecast = _period_value(period, "shortForecast", "short_forecast", default="")
    detailed_forecast = _period_value(period, "detailedForecast", "detailed_forecast", default="")

    if temperature is None:
        return f"{name}: {short_forecast} - {detailed_forecast}"

    return f"{name}: {short_forecast} - {temperature}{temperature_unit}. {detailed_forecast}"


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


def filter_alerts(alerts: list[Alert], config: GatewayConfig, location_zones: set[str] | None = None) -> list[Alert]:
    """Filter alerts to the configured alert types and local forecast zones when available."""
    filtered: list[Alert] = []
    local_zones = set(location_zones or set())

    for alert in alerts:
        if alert.event not in config.alert_types:
            continue

        if local_zones:
            alert_zones = {zone for zone in alert.zones if zone}
            if alert_zones and not alert_zones.intersection(local_zones):
                continue

        filtered.append(alert)

    return filtered
