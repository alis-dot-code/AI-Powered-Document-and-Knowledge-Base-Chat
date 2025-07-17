from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base application error."""

    def __init__(self, status_code: int, detail: str, code: str | None = None):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code or f"ERR_{status_code}"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, "UNAUTHORIZED")


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail, "FORBIDDEN")


class InvalidCredentialsError(AppError):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid email or password",
            "INVALID_CREDENTIALS",
        )


class InvalidTokenError(AppError):
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, "INVALID_TOKEN")


class EmailAlreadyExistsError(AppError):
    def __init__(self):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "An account with this email already exists",
            "EMAIL_EXISTS",
        )


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

class ValidationError(AppError):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail, "VALIDATION_ERROR")


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            f"{resource} not found",
            "NOT_FOUND",
        )


class ConflictError(AppError):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status.HTTP_409_CONFLICT, detail, "CONFLICT")


# ---------------------------------------------------------------------------
# Workspace / Permissions
# ---------------------------------------------------------------------------

class WorkspaceNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Workspace")


class WorkspaceAccessDeniedError(ForbiddenError):
    def __init__(self):
        super().__init__("You do not have access to this workspace")


class InsufficientRoleError(ForbiddenError):
    def __init__(self, required_role: str = "editor"):
        super().__init__(f"This action requires the '{required_role}' role or higher")


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class DocumentNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Document")


class UnsupportedFileTypeError(AppError):
    def __init__(self, mime_type: str = ""):
        super().__init__(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported file type: {mime_type}",
            "UNSUPPORTED_FILE_TYPE",
        )


class FileTooLargeError(AppError):
    def __init__(self, max_mb: int = 50):
        super().__init__(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds maximum size of {max_mb}MB",
            "FILE_TOO_LARGE",
        )


# ---------------------------------------------------------------------------
# Billing / Usage
# ---------------------------------------------------------------------------

class QuotaExceededError(AppError):
    def __init__(self, resource: str = "queries"):
        super().__init__(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Monthly {resource} quota exceeded. Please upgrade your plan.",
            "QUOTA_EXCEEDED",
        )


class SubscriptionRequiredError(AppError):
    def __init__(self, feature: str = "this feature"):
        super().__init__(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"A paid subscription is required for {feature}",
            "SUBSCRIPTION_REQUIRED",
        )


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

class InternalError(AppError):
    def __init__(self, detail: str = "An internal error occurred"):
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail,
            "INTERNAL_ERROR",
        )
