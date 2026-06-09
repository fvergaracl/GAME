from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class DuplicatedError(HTTPException):
    """
    Exception raised for duplicated entries.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the DuplicatedError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)


class NotFoundError(HTTPException):
    """
    Exception raised for not found entries.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the NotFoundError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)


class GoneError(HTTPException):
    """
    Exception raised for gone errors.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the GoneError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_410_GONE, detail, headers)


class ConflictError(HTTPException):
    """
    Exception raised for conflict errors.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the ConflictError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_409_CONFLICT, detail, headers)


class PreconditionFailedError(HTTPException):
    """
    Exception raised for precondition failed errors.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the PreconditionFailedError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_412_PRECONDITION_FAILED, detail, headers)


class InternalServerError(HTTPException):
    """
    Exception raised for internal server errors.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the InternalServerError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail, headers)


class ForbiddenError(HTTPException):
    """
    Exception raised for forbidden errors.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the ForbiddenError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_403_FORBIDDEN, detail, headers)


class TooManyRequestsError(HTTPException):
    """
    Exception raised for rate-limit and abuse-prevention violations.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the TooManyRequestsError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_429_TOO_MANY_REQUESTS, detail, headers)


# HTTP_400_BAD_REQUEST


class BadRequestError(HTTPException):
    """
    Exception raised for bad request errors.

    Attributes:
        detail (Any): The detail message for the exception.
        headers (Optional[Dict[str, Any]]): The headers for the exception
          response.
    """

    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initializes the BadRequestError with the provided details.

        Args:
            detail (Any, optional): The detail message for the exception.
            headers (Optional[Dict[str, Any]], optional): The headers for the
              exception response.
        """
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)


# DSL interpreter errors
# These inherit from the right HTTP base classes so FastAPI serialises them
# without an extra exception handler. We keep them as distinct types so the
# simulate/CRUD endpoints can map specific failure modes to clear messages and
# tests can assert on the precise class.
#
# Each DSL error optionally carries a stable ``code`` plus a
# ``params`` map. When ``code`` is supplied the ``detail`` body becomes a
# dict ``{"code": ..., "params": ..., "message": ...}`` so the frontend
# can render a localised message via i18n while servers, logs, and pytest
# assertions keep using the English ``message`` fallback. Legacy callers
# that pass a bare string keep their existing shape - FastAPI returns
# ``{"detail": "<string>"}`` exactly as before.


def _build_dsl_detail(
    *,
    detail: Any,
    code: Optional[str],
    params: Optional[Dict[str, Any]],
) -> Any:
    """
    Compose the ``detail`` body for a DSL error.

    When ``code`` is provided, return a structured dict the frontend can
    translate. Otherwise return ``detail`` unchanged so legacy raises
    that still pass a bare string serialise identically to pre-Sprint-10.
    """
    if code is None:
        return detail
    message = detail if isinstance(detail, str) else None
    return {
        "code": code,
        "params": dict(params or {}),
        "message": message,
    }


class _DslErrorMixin:
    """
    Shared init for DSL errors. Subclasses inherit from this *plus* the
    HTTP base class so FastAPI continues to see them as HTTPExceptions.
    """

    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
        *,
        code: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        body = _build_dsl_detail(detail=detail, code=code, params=params)
        # The HTTP base class lives next in the MRO; let it run the
        # actual HTTPException init with the composed detail.
        super().__init__(detail=body, headers=headers)  # type: ignore[misc]
        self.code = code
        self.params = dict(params or {})


class DslValidationError(_DslErrorMixin, BadRequestError):
    """AST is structurally invalid or references a path outside the whitelist."""


class DslExecutionError(_DslErrorMixin, BadRequestError):
    """Runtime DSL failure (division by zero, type mismatch, etc.)."""


class DslLimitExceededError(_DslErrorMixin, PreconditionFailedError):
    """AST tried to evaluate more nodes or recurse deeper than configured."""


class DslTimeoutError(_DslErrorMixin, PreconditionFailedError):
    """AST execution exceeded the configured wall-clock budget."""
