from typing import Annotated
from fastapi import APIRouter, Depends, File, UploadFile
from starlette.concurrency import run_in_threadpool
from app.core.exceptions import DomainError
from app.core.logging import log_event
from app.dependencies import CurrentUser
from app.schemas.image_prediction import ImagePredictionResponse
from app.services.cattle_image_classifier import CattleImageClassifier, get_image_classifier

router = APIRouter(prefix="/predict", tags=["AI-assisted screening"])


@router.post("/image", response_model=ImagePredictionResponse,
             description="Upload a cattle image for AI-assisted Healthy/FMD/Lumpy screening. "
                         "Supports only Healthy, Foot-and-Mouth Disease and Lumpy Skin Disease. "
                         "Requires a bearer token. Confidence is not diagnostic certainty.",
             responses={code: {"description": text} for code, text in {
                 400: "Missing, empty or invalid image", 401: "Authentication required",
                 413: "Image too large", 415: "Unsupported image type",
                 500: "Prediction failed", 503: "Image model unavailable"}.items()})
async def predict_image(user: CurrentUser,
                        service: Annotated[CattleImageClassifier, Depends(get_image_classifier)],
                        file: Annotated[UploadFile | None, File()] = None):
    if file is None:
        raise DomainError("MISSING_IMAGE", "An image file is required.", 400)
    try:
        if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            log_event("invalid_cattle_image_upload", reason="unsupported_mime")
            raise DomainError("UNSUPPORTED_IMAGE", "Unsupported image type.", 415)
        data = await file.read(service.settings.image_max_upload_bytes + 1)
        return await run_in_threadpool(service.predict, data)
    finally:
        await file.close()
