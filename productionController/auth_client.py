"""Authentication client for the productionController service.

Adapted from AI_ML_Service/core/auth_client.py (copied pattern, not imported).
Login returns only a JWT; user id is resolved via GET /auth/me afterward.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config import Settings

logger = logging.getLogger(__name__)


class AuthError(RuntimeError):
    """Raised when authentication against the backend fails."""


class AuthClient:
    """Manages JWT auth against the backend using PC_EMAIL / PC_PASSWORD."""

    LOGIN_PATH = "/auth/login"
    REFRESH_PATH = "/auth/refresh"
    ME_PATH = "/auth/me"

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self.authenticated_user_id: Optional[int] = None

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    async def login(self) -> None:
        """Authenticate and resolve the logged-in user id via /auth/me."""
        url = f"{self._settings.backend_base}{self.LOGIN_PATH}"
        payload = {
            "email": self._settings.PC_EMAIL,
            "password": self._settings.PC_PASSWORD,
        }
        try:
            resp = await self._client.post(url, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AuthError(f"Login failed: {exc}") from exc

        self._store_tokens(resp.json())
        await self._resolve_user_id()
        logger.info("Authenticated with backend as %s", self._settings.PC_EMAIL)

    async def ensure_authenticated(self) -> None:
        """Re-login if token is missing."""
        if not self._access_token:
            await self.login()

    async def refresh(self) -> None:
        """Refresh the access token; fall back to a full login if needed."""
        if not self._refresh_token:
            await self.login()
            return

        url = f"{self._settings.backend_base}{self.REFRESH_PATH}"
        try:
            resp = await self._client.post(
                url,
                json={"refresh_token": self._refresh_token},
                headers=self.get_headers(),
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

    async def _resolve_user_id(self) -> None:
        """GET /auth/me — login response does not include user id."""
        url = f"{self._settings.backend_base}{self.ME_PATH}"
        try:
            resp = await self._client.get(url, headers=self.get_headers())
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AuthError(f"Failed to resolve user id via /auth/me: {exc}") from exc

        data = resp.json()
        user_id = data.get("id")
        if user_id is None:
            raise AuthError("/auth/me response did not contain id")
        self.authenticated_user_id = int(user_id)

    def _store_tokens(self, data: dict) -> None:
        self._access_token = data.get("access_token") or data.get("accessToken")
        self._refresh_token = (
            data.get("refresh_token")
            or data.get("refreshToken")
            or self._refresh_token
        )
        # Some backends may embed user id in the login payload — prefer it if present.
        for key in ("user_id", "operator_id", "id"):
            if data.get(key) is not None and self.authenticated_user_id is None:
                try:
                    self.authenticated_user_id = int(data[key])
                except (TypeError, ValueError):
                    pass
        if isinstance(data.get("user"), dict) and data["user"].get("id") is not None:
            try:
                self.authenticated_user_id = int(data["user"]["id"])
            except (TypeError, ValueError):
                pass
        if not self._access_token:
            raise AuthError("Auth response did not contain an access token")
