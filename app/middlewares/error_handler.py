"""Catch-all error handler that keeps CORS headers on 500 responses.

Starlette builds its middleware stack with ``ServerErrorMiddleware`` as the
**outermost** layer, sitting *above* the user-added ``CORSMiddleware``. So an
unhandled exception (a real 500) is rendered by ``ServerErrorMiddleware`` and
never passes back through ``CORSMiddleware`` — the response ships **without**
``Access-Control-Allow-Origin``. The browser then blocks the cross-origin
response and the dashboard shows a bare *"Network Error"* instead of the real
status/message (see ``reference_network_error_means_500``).

This pure-ASGI middleware is installed *inside* ``CORSMiddleware`` (CORS is
added last in ``app/main.py`` so it stays outermost). It converts any
unhandled exception into a JSON ``500`` **within** the stack, so the response
flows back out through ``CORSMiddleware`` and gets its CORS headers. The
traceback is still logged (and forwarded to Sentry) so observability is
unchanged.

``HTTPException`` and its subclasses never reach here — Starlette's
``ExceptionMiddleware`` (also inside CORS) already turns them into proper 4xx
responses with CORS headers. Only genuine, unhandled errors are caught.
"""

import logging

import sentry_sdk
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class CatchUnhandledErrorsMiddleware:
    """Render unhandled exceptions as a JSON 500 from inside the stack."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            # websocket / lifespan — nothing to translate.
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message):
            """Track whether the response has started before forwarding it.

            Records the first ``http.response.start`` so the outer handler
            knows it can no longer safely replace the response with a 500.
            """
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:  # noqa: BLE001 - deliberate catch-all for 500s
            # Preserve observability: the traceback still reaches the logs and
            # Sentry even though we no longer let the exception bubble up to
            # ServerErrorMiddleware.
            logger.exception("Unhandled exception while handling request")
            sentry_sdk.capture_exception(exc)

            if response_started:
                # Headers/body already in flight — we cannot replace the
                # response; re-raise so the server tears the connection down.
                raise

            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
            await response(scope, receive, send)
