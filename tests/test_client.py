"""Tests for the SimpleAnalytics HTTP client."""

import httpx
import pytest
import respx

from simpleanalytics_mcp.client import API_VERSION, default_timezone, get_json


@respx.mock
async def test_get_json_injects_version_and_api_key() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={"pageviews": 5})
    )
    result = await get_json("/example.com.json", {"fields": "pageviews"}, need_user_id=False)
    assert result == {"pageviews": 5}
    request = route.calls.last.request
    assert request.url.params["version"] == API_VERSION
    assert request.url.params["fields"] == "pageviews"
    assert request.headers["Api-Key"] == "sa_api_key_test"
    assert "User-Id" not in request.headers


@respx.mock
async def test_get_json_sends_user_id_when_required() -> None:
    route = respx.get("https://simpleanalytics.com/api/websites").mock(
        return_value=httpx.Response(200, json=[])
    )
    await get_json("/api/websites", {}, need_user_id=True)
    request = route.calls.last.request
    assert request.headers["User-Id"] == "sa_user_id_test"


@respx.mock
async def test_get_json_maps_auth_error() -> None:
    respx.get("https://simpleanalytics.com/api/websites").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )
    with pytest.raises(ValueError, match="SA_API_KEY"):
        await get_json("/api/websites", {}, need_user_id=True)


@respx.mock
async def test_get_json_maps_generic_error() -> None:
    respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(400, text="bad param")
    )
    with pytest.raises(ValueError, match="400"):
        await get_json("/example.com.json", {}, need_user_id=False)


@respx.mock
async def test_get_json_maps_transport_error() -> None:
    respx.get("https://simpleanalytics.com/api/websites").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(ValueError, match="request failed"):
        await get_json("/api/websites", {}, need_user_id=True)


def test_default_timezone_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SA_DEFAULT_TIMEZONE", "Europe/Amsterdam")
    assert default_timezone() == "Europe/Amsterdam"


def test_default_timezone_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SA_DEFAULT_TIMEZONE", raising=False)
    assert default_timezone() == "America/Chicago"


def test_get_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from simpleanalytics_mcp.client import _get_api_key

    monkeypatch.delenv("SA_API_KEY", raising=False)
    with pytest.raises(ValueError, match="SA_API_KEY"):
        _get_api_key()
