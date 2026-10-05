class DomainError(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


class AnimalNotFound(DomainError):
    def __init__(self):
        super().__init__("ANIMAL_NOT_FOUND", "Animal not found.", 404)


class CaseNotFound(DomainError):
    def __init__(self):
        super().__init__("CASE_NOT_FOUND", "Case not found.", 404)


class PermissionDenied(DomainError):
    def __init__(self):
        super().__init__("PERMISSION_DENIED", "You do not have permission for this action.", 403)


class ModelUnavailable(DomainError):
    def __init__(self, message="The trained model is not available."):
        super().__init__("MODEL_NOT_AVAILABLE", message, 503)


class FeatureMismatch(DomainError):
    def __init__(self, message="Features do not match the verified model contract."):
        super().__init__("MODEL_FEATURE_MISMATCH", message, 422)


class DuplicateSubmission(DomainError):
    def __init__(self):
        super().__init__("IDEMPOTENCY_CONFLICT", "This key was already used with a different payload.", 409)
