==================================================
ADR 0009: Fail-fast env validation in prod/stage
==================================================

:Status: Accepted

Context
=======

Insecure development defaults - a wildcard CORS origin, a placeholder secret,
a fallback database name - leaking into a protected deployment is a classic
"works in dev, leaks in prod" hazard that is invisible until it is exploited.

Decision
========

Module-level validators run at import in ``app/core/config.py`` and raise
``ValueError`` (blocking boot) only when ``ENV`` is ``prod`` or ``stage``:
rejecting ``"*"`` in CORS, rejecting an empty ``SECRET_KEY`` or an
empty/placeholder ``KEYCLOAK_CLIENT_SECRET``, requiring ``DB_NAME`` (the old
``game_dev_db`` fallback was removed), and rejecting malformed trusted-proxy
CIDRs. In ``dev`` and ``test`` the validators early-return.

Consequences
============

* Misconfiguration becomes a loud startup failure instead of a silent runtime
  leak.
* ``prod``/``stage`` genuinely require these variables to be set; dev and the
  test suite are unaffected.

See also
========

* :doc:`/security` - "Secrets & fail-fast configuration".
* :doc:`/configuration` - every variable these checks guard.
