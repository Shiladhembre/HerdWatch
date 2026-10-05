from fastapi import APIRouter
from .routes import (
    auth,
    users,
    animals,
    herds,
    cases,
    predictions,
    outbreaks,
    vaccinations,
    treatments,
    laboratories,
    alerts,
    weather,
    analytics,
    locations,
    image_predictions,
)

router = APIRouter()
for module in [
    auth,
    users,
    animals,
    herds,
    cases,
    predictions,
    outbreaks,
    vaccinations,
    treatments,
    laboratories,
    alerts,
    weather,
    analytics,
    locations,
    image_predictions,
]:
    router.include_router(module.router)
