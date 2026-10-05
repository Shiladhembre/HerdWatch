from enum import StrEnum


class Role(StrEnum):
    FARMER = "FARMER"
    FIELD_WORKER = "FIELD_WORKER"
    VETERINARIAN = "VETERINARIAN"
    DISTRICT_OFFICER = "DISTRICT_OFFICER"
    ADMIN = "ADMIN"


class CaseStatus(StrEnum):
    REPORTED = "REPORTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SAMPLE_REQUESTED = "SAMPLE_REQUESTED"
    LAB_PENDING = "LAB_PENDING"
    CONFIRMED = "CONFIRMED"
    TREATMENT_ONGOING = "TREATMENT_ONGOING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Severity(StrEnum):
    ROUTINE = "ROUTINE"
    MODERATE = "MODERATE"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class LabStatus(StrEnum):
    REQUESTED = "REQUESTED"
    COLLECTED = "COLLECTED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    TESTING = "TESTING"
    RESULT_AVAILABLE = "RESULT_AVAILABLE"
    CLOSED = "CLOSED"


class Risk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


SPECIES = ["Cattle", "Buffalo", "Goat", "Sheep", "Pig", "Poultry", "Other"]
DISCLAIMER = "AI-assisted screening result. Veterinary confirmation is required."
