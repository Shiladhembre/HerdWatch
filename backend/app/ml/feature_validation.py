import math
from app.core.exceptions import FeatureMismatch
from app.core.symptom_config import FEATURE_CODES

LEAKAGE_FIELDS = {
    "event_confirmed_on",
    "deaths",
    "death_count",
    "killed",
    "slaughtered",
    "lab_results",
    "lab_result",
    "result",
    "post_outbreak_interventions",
    "event_status",
    "future_vaccination_interventions",
}


def symptom_vector(features, ordered):
    if set(ordered) != set(FEATURE_CODES) or len(ordered) != 18 or set(features) != set(ordered):
        raise FeatureMismatch()
    if any(type(v) is not int or v not in (0, 1) for v in features.values()):
        raise FeatureMismatch("Only integer 0/1 features are supported.")
    return [features[name] for name in ordered]


def risk_vector(payload, metadata):
    if set(payload.features) != set(metadata.features) or set(payload.observed_at) != set(metadata.features):
        raise FeatureMismatch("Supply exactly the model features and a timestamp for each.")
    if set(metadata.pre_outbreak_features) != set(metadata.features):
        raise FeatureMismatch("Pre-outbreak feature review is incomplete.")
    if any(name.lower() in LEAKAGE_FIELDS for name in payload.features):
        raise FeatureMismatch("Post-outbreak leakage fields are prohibited.")
    for name, value in payload.features.items():
        observed = payload.observed_at[name]
        if not observed.tzinfo or observed > payload.prediction_cutoff:
            raise FeatureMismatch("Features must be observed on or before the prediction cutoff.")
        if (payload.prediction_cutoff - observed).days > metadata.maximum_feature_age_days:
            raise FeatureMismatch("Feature is older than the model contract allows.")
        kind = metadata.feature_types.get(name)
        if kind == "number" and (
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        ):
            raise FeatureMismatch(f"{name} requires a finite numeric value.")
        if kind == "string" and not isinstance(value, str):
            raise FeatureMismatch(f"{name} requires a string.")
        if kind not in ("number", "string"):
            raise FeatureMismatch("Feature type metadata is incomplete.")
    return [payload.features[name] for name in metadata.features]
