import pandas as pd
from app.core.exceptions import ModelUnavailable, DomainError
from .feature_validation import risk_vector


def predict(slot, payload):
    if slot.model is None:
        raise ModelUnavailable(f"Outbreak model status: {slot.status}.")
    values = risk_vector(payload, slot.contract)
    try:
        result = str(slot.model.predict(pd.DataFrame([values], columns=slot.contract.features))[0]).upper()
        if result not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError("Unsupported class")
        return result
    except Exception:
        raise DomainError(
            "PREDICTION_FAILED", "The outbreak model could not produce a valid assessment.", 503
        ) from None
