from fastapi import APIRouter
from app.dependencies import DB, CurrentUser
from app.schemas.prediction import DiseaseInput, RiskInput, AssessmentView
from app.services import prediction_service
from app.core.symptom_config import SYMPTOMS
from app.utils.responses import Envelope, ok

router = APIRouter(prefix="/predict", tags=["AI-assisted screening"])


@router.post("/disease", response_model=Envelope[AssessmentView])
async def disease(payload: DiseaseInput, db: DB, user: CurrentUser):
    """Screen 18 ordered coded features. A prediction never confirms a diagnosis."""
    return ok(await prediction_service.disease(db, user, payload))


@router.post("/outbreak-risk", response_model=Envelope[AssessmentView])
async def outbreak(payload: RiskInput, db: DB, user: CurrentUser):
    """Uses only the verified trained feature contract and pre-cutoff observations."""
    return ok(await prediction_service.outbreak(db, user, payload))


@router.get("/symptom-config", response_model=Envelope[list[dict]])
async def symptom_config(user: CurrentUser):
    return ok(SYMPTOMS)
