import hashlib
import secrets
from typing import NamedTuple

DEFAULT_KEY_NAMESPACE = "gme_live_"
PREFIX_RANDOM_LEN = 8
SECRET_RANDOM_LEN = 32
LEGACY_PREFIX_NAMESPACE = "gme_legacy_"


class GeneratedApiKey(NamedTuple):
    """
    Output of :func:`generate_api_key`.

    Attributes:
        plaintext (str): Full key shown to the caller exactly once. Carries
            the public prefix concatenated with the secret payload.
        prefix (str): Public identifier safe to persist in DB columns and
            log streams (e.g. ``gme_live_abc12345``).
        key_hash (str): ``sha256(plaintext)`` hex digest. The canonical
            lookup value persisted in the database.
    """

    plaintext: str
    prefix: str
    key_hash: str


def hash_api_key(plaintext: str) -> str:
    """
    Return the canonical sha256 hex digest used to look up an API key.
    """
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def extract_prefix(plaintext: str) -> str:
    """
    Return the public prefix portion of an API-key plaintext.

    New-format keys carry a ``<namespace><body>.<secret>`` shape; the prefix
    is the portion before the dot. Legacy keys without a dot fall back to a
    deterministic, hash-derived identifier so they can still be referenced in
    logs without exposing the secret.
    """
    if "." in plaintext:
        return plaintext.split(".", 1)[0]
    return f"{LEGACY_PREFIX_NAMESPACE}{hash_api_key(plaintext)[:12]}"


def generate_api_key(namespace: str = DEFAULT_KEY_NAMESPACE) -> GeneratedApiKey:
    """
    Generate a cryptographically-secure API key.

    Returns:
        GeneratedApiKey: (plaintext, prefix, key_hash). Callers should display
        ``plaintext`` to the user exactly once, persist ``prefix`` (for FK
        references and logs) and ``key_hash`` (for O(1) auth lookups), and
        then discard the plaintext.
    """
    prefix_body = secrets.token_urlsafe(6)[:PREFIX_RANDOM_LEN]
    prefix = f"{namespace}{prefix_body}"
    secret = secrets.token_urlsafe(24)[:SECRET_RANDOM_LEN]
    plaintext = f"{prefix}.{secret}"
    return GeneratedApiKey(plaintext=plaintext, prefix=prefix, key_hash=hash_api_key(plaintext))
