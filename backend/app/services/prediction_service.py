from asyncio import to_thread
from app.models import Prediction, Case
from app.core.constants import DISCLAIMER, Role
from app.core.permissions import require_role
from app.core.exceptions import DomainError
from app.ml import symptom_predictor, outbreak_predictor
from app.ml.model_loader import registry
from app.repositories.base import get_scoped
from .audit_service import audit


async def disease(db, user, payload):
    require_role(user, Role.FARMER, Role.FIELD_WORKER, Role.VETERINARIAN)
    case = await get_scoped(db, Case, payload.case_id, user, lock=True) if payload.case_id else None
    if case and case.species != "Cattle":
        raise DomainError("UNSUPPORTED_SPECIES", "The symptom model supports cattle only.", 422)
    label, confidence = await to_thread(symptom_predictor.predict, registry.symptom, payload.symptoms)
    contract = registry.symptom.contract
    row = Prediction(
        case_id=payload.case_id,
        requested_by=user.id,
        model_name=contract.name,
        model_version=contract.version,
        input_features=payload.symptoms,
        predicted_class=label,
        probability=confidence,
    )
    db.add(row)
    await db.flush()
    priority = contract.triage_priorities.get(label, "REVIEW_REQUIRED")
    if case:
        case.suspected_disease = label
        if priority == "HIGH":
            case.risk_level = "HIGH"
        audit(db, user, "ai_assessment", case, {"prediction_id": str(row.id), "model_version": contract.version})
    return {
        "suspected_disease": label,
        "triage_priority": priority,
        "confidence": confidence,
        "confidence_calibrated": confidence is not None,
        "veterinary_confirmation_required": True,
        "model_version": contract.version,
        "disclaimer": DISCLAIMER,
        "reasons": [],
    }


async def outbreak(db, user, payload):
    require_role(user, Role.VETERINARIAN, Role.DISTRICT_OFFICER)
    result = await to_thread(outbreak_predictor.predict, registry.outbreak, payload)
    contract = registry.outbreak.contract
    db.add(
        Prediction(
            requested_by=user.id,
            model_name=contract.name,
            model_version=contract.version,
            input_features=payload.model_dump(mode="json"),
            predicted_class=result,
        )
    )
    return {
        "outbreak_risk": result,
        "confidence": None,
        "confidence_calibrated": False,
        "veterinary_confirmation_required": True,
        "model_version": contract.version,
        "disclaimer": DISCLAIMER,
        "reasons": [],
    }
