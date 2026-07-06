"""SimpleAnalytics API async HTTP client."""

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

SA_BASE = "https://simpleanalytics.com"
API_VERSION = "6"


def _get_api_key() -> str:
    key = os.environ.get("SA_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "SA_API_KEY environment variable is not set. "
            "Set it in your environment or in a .env file."
        )
    return key


def _get_user_id() -> str:
    user_id = os.environ.get("SA_USER_ID", "").strip()
    if not user_id:
        raise ValueError(
            "SA_USER_ID environment variable is not set. "
            "It is required for the Export API and list_websites."
        )
    return user_id


def default_timezone() -> str:
    """Return the configured default timezone (SA_DEFAULT_TIMEZONE)."""
    return os.environ.get("SA_DEFAULT_TIMEZONE", "America/Chicago")


async def get_json(path: str, params: dict[str, Any], *, need_user_id: bool) -> Any:
    """GET a SimpleAnalytics endpoint and return parsed JSON.

    Injects the pinned API version and the Api-Key header (plus User-Id when
    required). Maps non-2xx responses and transport errors to ValueError.
    """
    headers = {"Api-Key": _get_api_key()}
    if need_user_id:
        headers["User-Id"] = _get_user_id()

    query: dict[str, Any] = {"version": API_VERSION, **params}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{SA_BASE}{path}", params=query, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        detail = exc.response.text[:500]
        if status in (401, 403):
            raise ValueError(
                f"SimpleAnalytics auth failed ({status}). "
                f"Check SA_API_KEY and SA_USER_ID. {detail}"
            ) from exc
        raise ValueError(f"SimpleAnalytics API error {status}: {detail}") from exc
    except httpx.RequestError as exc:
        raise ValueError(f"SimpleAnalytics request failed: {exc}") from exc

    return response.json()
