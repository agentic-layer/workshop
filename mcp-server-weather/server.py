"""Weather MCP server.

Wraps the free Open-Meteo APIs (no API key required) and exposes a
handful of weather tools over MCP. The agent can ask for current
weather, a multi-day forecast, or look up a city's coordinates.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from fastmcp import FastMCP

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _describe(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return WEATHER_CODE.get(int(code), f"Weather code {code}")


async def _geocode(city: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(GEOCODE_URL, params={"name": city, "count": 1, "language": "en", "format": "json"})
        r.raise_for_status()
        results = (r.json() or {}).get("results") or []
        return results[0] if results else None


mcp = FastMCP(
    name="Weather MCP",
    instructions=(
        "Provides current weather and short-term forecasts for any city in "
        "the world using Open-Meteo. Always start with geocode_city() if "
        "you need coordinates; use get_current_weather() or get_forecast() "
        "directly with a city name for the common cases."
    ),
)


@mcp.tool()
async def geocode_city(city: str) -> dict[str, Any]:
    """Look up the latitude/longitude and country of a city name.

    Returns: { name, country, country_code, latitude, longitude, timezone }.
    Raises a ValueError if the city is not found.
    """
    hit = await _geocode(city)
    if hit is None:
        raise ValueError(f"City not found: {city!r}")
    return {
        "name": hit.get("name"),
        "country": hit.get("country"),
        "country_code": hit.get("country_code"),
        "latitude": hit.get("latitude"),
        "longitude": hit.get("longitude"),
        "timezone": hit.get("timezone"),
    }


@mcp.tool()
async def get_current_weather(city: str) -> dict[str, Any]:
    """Get the current weather for a city.

    Returns: { city, country, temperature_c, apparent_temperature_c,
    wind_speed_kmh, humidity_percent, conditions, time }.
    """
    place = await _geocode(city)
    if place is None:
        raise ValueError(f"City not found: {city!r}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        r.raise_for_status()
        cur = (r.json() or {}).get("current") or {}
    return {
        "city": place.get("name"),
        "country": place.get("country"),
        "temperature_c": cur.get("temperature_2m"),
        "apparent_temperature_c": cur.get("apparent_temperature"),
        "wind_speed_kmh": cur.get("wind_speed_10m"),
        "humidity_percent": cur.get("relative_humidity_2m"),
        "conditions": _describe(cur.get("weather_code")),
        "time": cur.get("time"),
    }


@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> dict[str, Any]:
    """Get a daily forecast for a city.

    Args:
        city: City name.
        days: How many days to forecast (1–7, default 3).

    Returns: { city, country, days: [{date, conditions, max_c, min_c,
    precipitation_mm, max_wind_kmh}] }.
    """
    if not 1 <= days <= 7:
        raise ValueError("`days` must be between 1 and 7.")
    place = await _geocode(city)
    if place is None:
        raise ValueError(f"City not found: {city!r}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "forecast_days": days,
                "timezone": "auto",
            },
        )
        r.raise_for_status()
        daily = (r.json() or {}).get("daily") or {}
    dates = daily.get("time") or []
    out = []
    for i, date in enumerate(dates):
        out.append({
            "date": date,
            "conditions": _describe((daily.get("weather_code") or [None])[i]),
            "max_c": (daily.get("temperature_2m_max") or [None])[i],
            "min_c": (daily.get("temperature_2m_min") or [None])[i],
            "precipitation_mm": (daily.get("precipitation_sum") or [None])[i],
            "max_wind_kmh": (daily.get("wind_speed_10m_max") or [None])[i],
        })
    return {"city": place.get("name"), "country": place.get("country"), "days": out}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
