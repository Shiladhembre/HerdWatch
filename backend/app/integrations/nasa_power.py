import asyncio
import math
import httpx
from app.config import get_settings
from app.core.exceptions import DomainError

PARAMETERS = {"T2M", "T2M_MAX", "T2M_MIN", "RH2M", "PRECTOTCORR"}


def parse_weather(payload, requested):
    raw = payload.get("properties", {}).get("parameter", {})
    if not isinstance(raw, dict):
        raise DomainError("WEATHER_INVALID", "The weather provider returned an invalid response.", 502)
    result = {}
    for name in requested:
        values = raw.get(name)
        if values is None:
            result[name] = None
            continue
        if not isinstance(values, dict):
            raise DomainError("WEATHER_INVALID", "Invalid weather series.", 502)
        parsed = {}
        for day, value in values.items():
            if len(day) != 8 or not day.isdigit():
                raise DomainError("WEATHER_INVALID", "Invalid weather date.", 502)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                parsed[day] = None
            else:
                parsed[day] = None if value <= -900 else value
        result[name] = parsed
    if not any(v and any(x is not None for x in v.values()) for v in result.values()):
        raise DomainError("WEATHER_UNAVAILABLE", "No valid observations are available for this request.", 503)
    return result


async def fetch(latitude, longitude, start_date, end_date, parameters, client=None):
    own = client is None
    client = client or httpx.AsyncClient(timeout=httpx.Timeout(15, connect=5), follow_redirects=False)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "parameters": ",".join(parameters),
        "community": "AG",
        "format": "JSON",
    }
    try:
        for attempt in range(3):
            try:
                response = await client.get(
                    get_settings().nasa_power_base_url + "/api/temporal/daily/point", params=params
                )
                response.raise_for_status()
                return {
                    "source": "NASA POWER",
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "parameters": parse_weather(response.json(), parameters),
                    "units": {
                        k: v.get("units")
                        for k, v in response.json().get("parameters", {}).items()
                        if isinstance(v, dict)
                    },
                }
            except (httpx.HTTPError, ValueError):
                if attempt == 2:
                    raise DomainError(
                        "WEATHER_PROVIDER_UNAVAILABLE", "NASA POWER is unavailable or returned invalid data.", 503
                    ) from None
                await asyncio.sleep(0.3 * 2**attempt)
    finally:
        if own:
            await client.aclose()
