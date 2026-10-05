import re
import unicodedata

DISEASE_ALIASES = {
    "antraks": "Anthrax",
    "anthrax": "Anthrax",
    "foot and mouth disease": "Foot and Mouth Disease",
    "mastitis": "Mastitis",
    "surra": "Surra",
    "piroplasmosis": "Piroplasmosis",
    "leptospirosis": "Leptospirosis",
}


def normalized(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or "")).strip()).casefold()


def disease_name(value):
    original = re.sub(r"\s+", " ", str(value or "").strip())
    return DISEASE_ALIASES.get(normalized(original), original)
