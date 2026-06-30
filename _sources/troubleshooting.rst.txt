===============
Troubleshooting
===============

.. admonition:: Who is this page for?
   :class: note

   Anyone who hits an error running, deploying, or calling GAME. This is the
   single home for known symptoms; they are grouped by where they show up -
   local setup, authentication, and runtime/integration. For the *why* behind
   the configuration guards see :doc:`configuration`, and for the request flow
   see :doc:`architecture`.

Local setup & first run
=======================

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Symptom
     - Likely cause / fix
   * - ``command not found: uvicorn``
     - ``uvicorn`` is installed inside the Poetry virtualenv, not globally. Run
       it through Poetry: ``poetry run uvicorn app.main:app --reload``. If it is
       still missing, ``poetry install`` to sync the environment with
       ``pyproject.toml``.
   * - App won't boot in ``prod``/``stage``
     - A fail-fast secret check tripped. The error names the missing variable
       (``SECRET_KEY``, ``KEYCLOAK_CLIENT_SECRET``, ``DB_NAME``) or rejects a
       wildcard ``BACKEND_CORS_ORIGINS=*``. See the *Fail-fast guards* table in
       :doc:`configuration`.
   * - ``404`` on a freshly created game
     - You addressed it with your ``externalGameId`` instead of the internal
       ``gameId`` the create call returned. URLs that target a specific record
       use the internal UUID. See :doc:`domain-model`.

Authentication
==============

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Symptom
     - Likely cause / fix
   * - ``401 Invalid authentication credentials``
     - No/invalid ``X-API-Key`` header **and** no valid OAuth2 bearer token.
       Check the credential and, for token flows, the realm setup in
       :doc:`authentication`.
   * - Token expired
     - Two options: (1) log out and back in to obtain a fresh token; or
       (2) raise the token lifetime in Keycloak - select your realm, open
       **Clients**, pick your client, then on the **Advanced** tab change
       **Access Token Lifespan** to the desired value.

Runtime & integration
=====================

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Symptom
     - Likely cause / fix
   * - Dashboard shows "Network Error"
     - Usually a backend ``500`` whose body the browser dropped because the
       error response carried no CORS headers. Check the API logs
       (``docker logs GAME_API_DEV``) for the real traceback rather than
       trusting the browser message. The middleware ordering behind this is
       explained in :doc:`architecture`.

Still stuck?
============

Open a `GitHub issue <https://github.com/fvergaracl/GAME/issues>`_ with your
version/commit, the endpoint and method, whether the strategy is a built-in
class or a DSL strategy, your deployment mode, and the relevant
``docker logs`` output. For a security problem, follow the
:doc:`security` policy instead of filing a public issue.
