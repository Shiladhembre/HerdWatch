FEATURE_CODES = [f"G{i:02}" for i in range(1, 19)]
SYMPTOMS = [
    {
        "modelFeature": code,
        "label": "Configure symptom name",
        "description": "Awaiting verified mapping",
        "verified": False,
    }
    for code in FEATURE_CODES
]
