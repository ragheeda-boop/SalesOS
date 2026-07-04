"""Base SDK exceptions used across all modules."""


class SalesOsError(Exception):
    """Base exception for all SalesOS errors."""


class ObjectNotFoundError(SalesOsError):
    """Raised when a domain entity is not found."""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class DuplicateObjectError(SalesOsError):
    """Raised when a duplicate entity is detected."""

    def __init__(self, entity_type: str, field: str, value: str):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} with {field} '{value}' already exists")


class ValidationError(SalesOsError):
    """Raised when domain validation fails."""

    def __init__(self, message: str, errors: list | None = None):
        self.errors = errors or []
        super().__init__(message)


class InvalidStateTransitionError(SalesOsError):
    """Raised when an invalid domain state transition is attempted."""

    def __init__(self, entity: str, from_state: str, to_state: str):
        super().__init__(f"Cannot transition {entity} from '{from_state}' to '{to_state}'")


class PermissionDeniedError(SalesOsError):
    """Raised when a user lacks permission for an action."""

    def __init__(self, user_id: str, permission: str):
        super().__init__(f"User {user_id} lacks permission: {permission}")


class ConfigurationError(SalesOsError):
    """Raised when system configuration is invalid."""

    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}")
