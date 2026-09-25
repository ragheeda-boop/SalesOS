"""Contact-domain exceptions used by duplicate-sensitive workflows."""

from fastapi import HTTPException, status


class AmbiguousContactMatchError(HTTPException):
    """A contact upsert key matched multiple tenant rows and needs review."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Multiple contacts match this tenant identity; manual review is required",
        )
