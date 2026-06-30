"""Authentication client for the backend API.

Handles service-account login, token storage, refresh, and automatic
re-authentication when a request comes back as 401. All endpoints and
credentials are config-driven (see core.config).
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from core.config import Settings

logger = logging.getLogger(__name__)


class AuthError(RuntimeError):
    """Raised when authentication against the backend fails."""


class AuthClient:
    """Manages access/refresh tokens against the backend auth endpoints."""

    LOGIN_PATH = "/auth/login"
    REFRESH_PATH = "/auth/refresh"

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    async def login(self) -> None:
        """Authenticate with the service account and store tokens."""
        url = f"{self._settings.backend_base}{self.LOGIN_PATH}"
        payload = {
            "email": self._settings.ML_SERVICE_EMAIL,
            "password": self._settings.ML_SERVICE_PASSWORD,
        }
        try:
            resp = await self._client.post(url, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AuthError(f"Login failed: {exc}") from exc

        self._store_tokens(resp.json())
        logger.info("Authenticated with backend as %s", self._settings.ML_SERVICE_EMAIL)

    async def refresh(self) -> None:
        """Refresh the access token; fall back to a full login if needed."""
        if not self._refresh_token:
            await self.login()
            return

        url = f"{self._settings.backend_base}{self.REFRESH_PATH}"
        try:
            resp = await self._client.post(
                url, json={"refresh_token": self._refresh_token}
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Token refresh failed (%s); retrying full login", exc)
            await self.login()
            return

        self._store_tokens(resp.json())
        logger.debug("Access token refreshed")

    def get_headers(self) -> dict[str, str]:
        """Return Authorization headers for authenticated requests."""
        if not self._access_token:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}

    def _store_tokens(self, data: dict) -> None:
        """Extract tokens from an auth response, tolerant of field naming."""
        self._access_token = data.get("access_token") or data.get("accessToken")
        self._refresh_token = (
            data.get("refresh_token")
            or data.get("refreshToken")
            or self._refresh_token
        )
        if not self._access_token:
            raise AuthError("Auth response did not contain an access token")
