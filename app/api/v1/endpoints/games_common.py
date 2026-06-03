from typing import Optional
from uuid import uuid4

import jwt
from fastapi import HTTPException, Request, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError

from app.core.exceptions import (ConflictError, DuplicatedError, InternalServerError,
                                 NotFoundError, PreconditionFailedError)


def _extract_api_key_from_header(api_key_header) -> Optional[str]:
    return getattr(getattr(api_key_header, "data", None), "apiKey", None)


def _game_access_kwargs(
    api_key: Optional[str],
    oauth_user_id: Optional[str],
    is_admin: bool = False,
) -> dict:
    return {
        "api_key": api_key,
        "oauth_user_id": oauth_user_id,
        "is_admin": is_admin,
        "enforce_scope": True,
    }


def _extract_oauth_user_id_from_token(token: str) -> Optional[str]:
    """
    Extracts `sub` from a bearer token without re-validating against Keycloak.

    Token validation is already enforced by `auth_api_key_or_oauth2` dependency.
    This avoids a second network-bound validation per request on write endpoints.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
            },
        )
    except jwt.PyJWTError:
        return None

    subject = payload.get("sub")
    if isinstance(subject, str) and subject.strip():
        return subject
    return None


def _resolve_correlation_id(request: Request) -> str:
    """
    Resolves correlation id from headers or creates one when missing.
    """
    if request is not None:
        header_value = request.headers.get("X-Correlation-ID") or request.headers.get(
            "x-correlation-id"
        )
        if header_value and header_value.strip():
            return header_value.strip()
    return f"srv-{uuid4()}"


def _resolve_idempotency_key(request: Request) -> Optional[str]:
    """
    Resolves idempotency key from common headers.
    """
    if request is None:
        return None
    key = request.headers.get("Idempotency-Key") or request.headers.get(
        "X-Idempotency-Key"
    )
    if key and key.strip():
        return key.strip()
    return None


def _extract_db_error_code(exc: Exception) -> Optional[str]:
    orig = getattr(exc, "orig", None)
    if orig is None:
        return None
    pgcode = getattr(orig, "pgcode", None)
    if pgcode:
        return str(pgcode)
    return None


def _map_write_exception(
    exc: Exception,
    *,
    correlation_id: str,
):
    if isinstance(exc, NotFoundError):
        return exc
    if isinstance(exc, ConflictError):
        return exc
    if isinstance(exc, DuplicatedError):
        return ConflictError(
            detail="Duplicate write detected for this resource. Use a new idempotency key."
        )
    if isinstance(exc, PreconditionFailedError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.detail,
        )
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, (KeyError, TypeError, ValueError, DataError)):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid request data for this operation.",
        )
    if isinstance(exc, IntegrityError):
        pgcode = _extract_db_error_code(exc)
        if pgcode == "23503":
            return NotFoundError(
                detail="Referenced resource not found for write operation."
            )
        if pgcode == "23505":
            return ConflictError(detail="Concurrent write conflict detected.")
        if pgcode in {"22P02", "22001", "22003"}:
            return HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid value provided for write operation.",
            )
        return ConflictError(detail="Write conflict detected.")
    if isinstance(exc, ProgrammingError):
        return ConflictError(
            detail=(
                "Database schema mismatch detected in write path. "
                "Run migrations and retry."
            )
        )
    return InternalServerError(
        detail=(
            "Internal error in write operation. "
            f"Please retry with correlationId={correlation_id}"
        )
    )
