import math
import pandas as pd
from app.config import get_settings
from app.core.exceptions import ModelUnavailable, DomainError
from .feature_validation import symptom_vector


def predict(slot, features):
    if slot.model is None:
        raise ModelUnavailable(f"Symptom model status: {slot.status}.")
    ordered = symptom_vector(features, slot.contract.features)
    frame = pd.DataFrame([ordered], columns=slot.contract.features)
    try:
        encoded = slot.model.predict(frame)
        label = str(slot.encoder.inverse_transform(encoded)[0] if slot.encoder is not None else encoded[0])
        if label not in slot.contract.classes:
            raise ValueError("Unsupported prediction class")
        confidence = None
        if get_settings().enable_model_confidence and slot.contract.calibrated and hasattr(slot.model, "predict_proba"):
            classes = list(map(str, slot.encoder.inverse_transform(slot.model.classes_)
                               if slot.encoder is not None else slot.model.classes_))
            value = float(slot.model.predict_proba(frame)[0][classes.index(label)])
            if math.isfinite(value) and 0 <= value <= 1:
                confidence = value
        return label, confidence
    except Exception:
        raise DomainError("PREDICTION_FAILED", "The model could not produce a valid assessment.", 503) from None
