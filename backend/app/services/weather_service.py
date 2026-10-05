import hashlib
import json
from datetime import date
from app.core.exceptions import DomainError
from app.integrations.nasa_power import PARAMETERS, fetch
from .cache import cache


async def get_weather(latitude, longitude, start_date, end_date, parameters):
    if start_date > end_date or end_date > date.today() or (end_date - start_date).days > 366:
        raise DomainError("INVALID_DATE_RANGE", "Use a past date range no longer than 366 days.", 422)
    names = sorted(set(parameters.split(",")))
    if not names or not set(names) <= PARAMETERS:
        raise DomainError(
            "INVALID_WEATHER_PARAMETERS", "Only T2M, T2M_MAX, T2M_MIN, RH2M and PRECTOTCORR are supported.", 422
        )
    key = (
        "weather:"
        + hashlib.sha256(json.dumps([latitude, longitude, str(start_date), str(end_date), names]).encode()).hexdigest()
    )
    async with cache.lock:
        value = await cache.get(key)
        if value:
            return {**value, "cached": True}
        result = await fetch(latitude, longitude, start_date, end_date, names)
        await cache.set(key, result, 21600)
        return {**result, "cached": False}
