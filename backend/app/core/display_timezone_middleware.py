import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.datetime_utils import convert_datetimes_for_api_response

logger = logging.getLogger("app.display_timezone")

_SKIP_PREFIXES = (
    "/docs",
    "/openapi.json",
    "/redoc",
)


class DisplayTimezoneMiddleware(BaseHTTPMiddleware):
    """Convert UTC datetime strings in JSON responses to the display timezone."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if request.url.path.startswith(_SKIP_PREFIXES):
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if not body:
            return response

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=_response_headers(response),
                media_type=response.media_type,
            )

        try:
            converted = convert_datetimes_for_api_response(payload)
        except Exception:
            logger.exception("Display timezone conversion failed; returning original payload")
            converted = payload
        return JSONResponse(
            content=converted,
            status_code=response.status_code,
            headers=_response_headers(response),
        )


def _response_headers(response: Response) -> dict[str, str]:
    headers = dict(response.headers)
    headers.pop("content-length", None)
    # Keep CORS / security headers when rebuilding the JSON body.
    return headers
