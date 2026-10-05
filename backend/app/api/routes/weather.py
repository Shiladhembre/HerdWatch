from datetime import date
from typing import Annotated
from fastapi import APIRouter, Query
from app.dependencies import CurrentUser
from app.services.weather_service import get_weather
from app.utils.responses import Envelope, ok

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", response_model=Envelope[dict])
async def weather(
    user: CurrentUser,
    latitude: Annotated[float, Query(ge=-90, le=90, allow_inf_nan=False)],
    longitude: Annotated[float, Query(ge=-180, le=180, allow_inf_nan=False)],
    start_date: date,
    end_date: date,
    parameters: str = "T2M,RH2M,PRECTOTCORR",
):
    """Cached NASA POWER observations; missing variables remain null, never synthetic."""
    return ok(await get_weather(latitude, longitude, start_date, end_date, parameters))
