# Weather MCP Server

Small MCP server that wraps the free [Open-Meteo](https://open-meteo.com/)
APIs. Used in the workshop's "author your own Agent" exercise — gives
participant agents a real third-party data source without dragging in
an API-key story.

No API key required.

## Setup

```bash
uv sync
```

## Run

```bash
uv run python server.py
```

Starts on `http://0.0.0.0:8000` with Streamable HTTP transport.

## Tools

| Tool | Purpose | Example |
|---|---|---|
| `geocode_city(city)` | Resolve a city name to latitude/longitude/country | "Find coordinates for Berlin" |
| `get_current_weather(city)` | Current temperature, conditions, wind, humidity | "How's the weather in Tokyo?" |
| `get_forecast(city, days=3)` | Daily forecast (1–7 days) | "3-day forecast for Reykjavík" |

Each call geocodes the city (Open-Meteo's geocoding API) and then hits
the forecast API. The returned objects use `temperature_c`,
`wind_speed_kmh`, etc. — explicit units so the agent can present them
clearly.

## Image

Built from this directory; published to
`ghcr.io/agentic-layer/workshop/weather-mcp` by
`.github/workflows/release-weather-mcp.yml`.
