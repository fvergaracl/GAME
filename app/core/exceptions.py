from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class DuplicatedError(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)


class UnauthorizedError(HTTPException):
    def __init__(
            self,
            detail: Any = "Unauthorized",
            headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED,
                         detail=detail, headers=headers)


class ForbiddenError(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, headers)


class NotFoundError(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)


class MethodNotAllowedError(HTTPException):
    def __init__(
            self,
            detail: Any = "Method Not Allowed",
            headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                         detail=detail, headers=headers)


class RequestTimeoutError(HTTPException):
    def __init__(
            self,
            detail: Any = "Request Timeout",
            headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status_code=status.HTTP_408_REQUEST_TIMEOUT,
                         detail=detail, headers=headers)


class ConflictError(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, headers)


class ValidationError(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail, headers)

# 412 Precondition Failed


class PreconditionFailedError(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_412_PRECONDITION_FAILED, detail, headers)


class InternalServerError(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail, headers)
