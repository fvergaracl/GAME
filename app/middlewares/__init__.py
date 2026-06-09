"""Middleware & request-scoped dependencies.

Cross-cutting request concerns: authentication (API key / OAuth2 bearer),
the per-request :class:`app.middlewares.auth_context.AuthContext` and audit
logger, JWT validation against Keycloak's JWKS, and the unhandled-error
handler that ensures even a ``500`` is rendered with CORS headers. See
:doc:`authentication </authentication>` and :doc:`security </security>`.
"""
