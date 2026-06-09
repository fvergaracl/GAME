==============
Authentication
==============

.. admonition:: Who is this page for?
   :class: note

   Integrators choosing a credential, and anyone debugging a ``401``/``403``.
   The enforcement internals (scoping, rate limits, secrets) live in
   :doc:`security`.

Two credentials, one decision
=============================

Almost every endpoint is guarded by the dependency
``auth_api_key_or_oauth2``. It accepts **either**:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Credential
     - Header
     - Best for
   * - **API key**
     - ``X-API-Key: <key>``
     - Server-to-server integration. Simple, long-lived, scoped to the data
       the key created.
   * - **OAuth2 bearer**
     - ``Authorization: Bearer <jwt>``
     - Interactive users/admins via Keycloak (OIDC). Required for
       privileged and per-user operations.

The resolution order is **API key first, OAuth2 second**: if a valid
``X-API-Key`` is present the request is authenticated immediately; otherwise
the bearer token is validated. If neither is valid the request fails with
``401 Invalid authentication credentials``.

.. note::

   A handful of endpoints require **OAuth2 specifically** and reject API keys —
   notably the per-user *simulation* endpoint
   (``GET /games/{gameId}/users/{externalUserId}/points/simulated``), which is
   bound to the token's own subject. Those endpoints use the stricter
   ``auth_oauth2`` dependency. The endpoint's OpenAPI entry always states
   which it requires.

API keys
========

Issuing a key
-------------

Keys are minted by ``POST /api/v1/apikey/create``, which is itself
OAuth2-protected — so you need a bearer token (and the admin role) to create
one:

.. code-block:: bash

   curl -s -X POST "http://localhost:8000/api/v1/apikey/create" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"client":"my-service"}'

The response contains the ``apiKey`` string. Store it as a secret; it is the
bearer of all authority for that ``client``.

Using a key
-----------

Send it on every request:

.. code-block:: bash

   curl -s "http://localhost:8000/api/v1/games" -H "X-API-Key: $API_KEY"

Properties to know:

* A key can be **active** or inactive. An inactive/unknown key yields
  ``403 API key is invalid or does not exist``.
* Validation results are **cached** briefly (``API_KEY_HEADER_CACHE_TTL_SECONDS``,
  default 5 s) to avoid a DB hit per request. With the default in-memory cache
  each worker caches independently, so a revocation propagates on the next
  request after the TTL; set ``APIKEY_CACHE_BACKEND=redis`` to share the cache
  (and revocations) across workers. See :doc:`configuration`.
* Every write made with a key stamps ``apiKey_used`` on the row, which both
  builds an audit trail and **scopes** what that key can later read (see
  :doc:`security`).

.. warning::

   The current API has no key *revoke/delete* endpoint. Treat key issuance as
   deliberate, and prefer one key per integration/``client`` so you can reason
   about blast radius.

OAuth2 with Keycloak
====================

GAME validates **RS256** JWTs issued by Keycloak (OpenID Connect). The
validation (``app/middlewares/valid_access_token.py``) is strict:

#. The signing key is fetched from the realm JWKS endpoint
   (``/realms/<realm>/protocol/openid-connect/certs``) via a ``PyJWKClient``
   that caches keys for 300 s.
#. The token is decoded and checked for:

   * **signature** (RS256, against the JWKS key),
   * **issuer** = ``<KEYCLOAK_URL>/realms/<KEYCLOAK_REALM>``,
   * **audience** = ``KEYCLOAK_AUDIENCE`` (default ``account``),
   * **expiry**, with 30 s of clock-skew leeway.

#. The **subject** is taken from ``sub``, falling back through
   ``preferred_username``, ``email``, ``client_id``, ``azp`` — so both user
   and service-account tokens resolve to a stable subject.

Failure modes map to precise responses:

.. list-table::
   :header-rows: 1
   :widths: 40 18 42

   * - Condition
     - Status
     - Detail
   * - Invalid signature
     - ``401``
     - ``Invalid token signature``
   * - Expired token
     - ``401``
     - ``Token has expired``
   * - Wrong audience
     - ``403``
     - ``Invalid audience``
   * - Other malformed token
     - ``401``
     - ``Invalid token``
   * - JWKS fetch failure
     - ``500``
     - ``Internal server error``

Getting a token (dev)
---------------------

For local development you can use the resource-owner password grant:

.. code-block:: bash

   TOKEN=$(curl -s -X POST \
     "$KEYCLOAK_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=$KEYCLOAK_CLIENT_ID" \
     -d "client_secret=$KEYCLOAK_CLIENT_SECRET" \
     -d "grant_type=password" \
     -d "username=game_admin" \
     -d "password=$KEYCLOAK_USER_WITH_ROLE_PASSWORD" | jq -r '.access_token')

Swagger UI at ``/docs`` is also wired for the OAuth2 authorization-code flow
when ``KEYCLOAK_CLIENT_ID``/``KEYCLOAK_CLIENT_SECRET`` are configured, so you
can authorize interactively and try endpoints in the browser.

The admin role
==============

A bearer token carrying the realm role **``AdministratorGAME``** is treated as
an **admin**. Admins bypass the per-key/per-subject data scoping described in
:doc:`security` and can perform privileged operations (such as issuing API
keys). Non-admin tokens are scoped to the games and users associated with
their subject.

Identity bootstrapping
======================

The first time a valid token is seen for a new subject, GAME creates an
``OAuthUsers`` record (``provider=keycloak``, ``status=active``) and writes a
single ``auth / OAuth user bootstrapped`` audit log entry. No manual user
provisioning is required — authenticating once is enough to register the
identity.

The per-request auth context
============================

Internally, every guarded handler receives an ``AuthContext`` (and an
``AuditLogger`` bound to it) carrying:

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Field
     - Meaning
   * - ``api_key``
     - The validated API key string, if one was presented.
   * - ``oauth_user_id``
     - The token subject (``sub``/fallback), if a bearer token was presented.
   * - ``is_admin``
     - Whether the token carries ``AdministratorGAME``.
   * - ``token_data``
     - The decoded JWT claims.

Handlers pass these into services as scoping parameters
(``api_key``, ``oauth_user_id``, ``is_admin``), which is how authorization is
enforced consistently across the codebase. See :doc:`security` for the exact
rules.

Quick reference
===============

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - You see…
     - It means…
   * - ``401 Invalid authentication credentials``
     - No valid ``X-API-Key`` and no valid bearer token were presented.
   * - ``403 API key is invalid or does not exist``
     - The ``X-API-Key`` was rejected (unknown/inactive).
   * - ``403 You do not have permission to access this game``
     - Authenticated, but the credential is scoped away from that game.
   * - ``429``
     - Authenticated, but a rate limit / daily quota was exceeded
       (:doc:`security`).
