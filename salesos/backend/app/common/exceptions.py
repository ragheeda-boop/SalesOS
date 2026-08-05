from fastapi import HTTPException, status

from app.config import settings


def safe_error_detail(exc: Exception, default: str = "An unexpected error occurred") -> str:
    """Return a safe error message, hiding internals in production."""
    if settings.env == "production":
        return default
    return str(exc)


class NotFoundError(HTTPException):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity} with id '{entity_id}' not found",
        )


class DuplicateError(HTTPException):
    def __init__(self, entity: str, field: str, value: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{entity} with {field} '{value}' already exists",
        )


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ValidationError(HTTPException):
    def __init__(self, errors: list):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors,
        )


def is_tenant_isolation_failure(exc: BaseException) -> bool:
    """Detect RLS / aborted-transaction failures that must not be soft-swallowed.

    Empty success responses for these errors can hide tenancy misconfiguration
    and must not be mistaken for "no timeline events".
    """
    msg = str(exc).lower()
    name = type(exc).__name__.lower()
    markers = (
        "row-level security",
        "row level security",
        "infailedsqltransactionerror",
        "infailedsqltransaction",
        "current transaction is aborted",
        "insufficientprivilege",
        "permission denied for table",
    )
    return any(m in msg or m in name for m in markers)

