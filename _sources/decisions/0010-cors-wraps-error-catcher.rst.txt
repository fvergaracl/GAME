====================================================
ADR 0010: CORS middleware wraps the error catcher
====================================================

:Status: Accepted

Context
=======

Starlette's default error middleware is outermost, so a real ``500`` ships
*without* CORS headers. A browser then drops the response and the dashboard
shows a bare "Network Error" with no status - hiding the actual backend fault.

Decision
========

A pure-ASGI ``CatchUnhandledErrorsMiddleware`` is registered **first** and
``CORSMiddleware`` **second** (``app/main.py``). Because ``add_middleware``
prepends, CORS ends up **outermost** and wraps the catcher. The catcher
converts an unhandled exception into a JSON ``500`` *from inside* the stack, so
the response flows back out through CORS and gets its ``Access-Control-Allow-*``
headers; the traceback is still logged and sent to Sentry.

Consequences
============

* Error responses keep their CORS headers, so the browser (and the dashboard)
  see the real ``500`` instead of an opaque "Network Error".
* The registration order is load-bearing and easy to break, so the *why* is
  documented next to the registration.

See also
========

* :doc:`/architecture` - "The middleware stack (and a subtle ordering bug it
  fixes)".
* :doc:`/troubleshooting` - the "Network Error" symptom.
