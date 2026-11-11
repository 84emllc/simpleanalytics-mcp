"""Tests for the get_recent_hits tool."""

from datetime import UTC, datetime

import httpx
import pytest
import respx
from fastmcp import FastMCP

from simpleanalytics_mcp.tools import recent
from simpleanalytics_mcp.tools.recent import register_recent_tools

EXPORT_URL = "https://simpleanalytics.com/api/export/datapoints"
NOW = datetime(2026, 11, 11, 16, 20, tzinfo=UTC)


async def _recent(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(recent, "utc_now", lambda: NOW)
    mcp = FastMCP("test")
    register_recent_tools(mcp)
    return (await mcp.get_tool("get_recent_hits")).fn


def _respond(request: httpx.Request) -> httpx.Response:
    hour = request.url.params["start"]
    rows = {
        "2026-11-11T09": [
            {"added_iso": "2026-11-11T15:10:00.000Z", "datapoint": "pageview"},
            {"added_iso": "2026-11-11T15:30:00.000Z", "datapoint": "signup"},
        ],
        "2026-11-11T10": [
            {"added_iso": "2026-11-11T16:05:00.000Z", "datapoint": "pageview"},
            {"added_iso": "2026-11-11T16:15:00.000Z", "datapoint": "pageview"},
        ],
    }
    return httpx.Response(200, json={"datapoints": rows.get(hour, [])})


@respx.mock
async def test_recent_hits_last_hour_newest_first(monkeypatch: pytest.MonkeyPatch) -> None:
    route = respx.get(EXPORT_URL).mock(side_effect=_respond)
    get_recent_hits = await _recent(monkeypatch)
    result = await get_recent_hits(hostname="example.com")
    requested = sorted(
        (c.request.url.params["start"], c.request.url.params["end"]) for c in route.calls
    )
    assert requested == [("2026-11-11T09", "2026-11-11T09"), ("2026-11-11T10", "2026-11-11T10")]
    params = route.calls.last.request.url.params
    assert params["robots"] == "true"
    assert params["type"] == "all"
    assert result["since"] == "2026-11-11T15:20:00Z"
    assert result["count"] == 3
    assert [h["added_iso"] for h in result["hits"]] == [
        "2026-11-11T16:15:00.000Z",
        "2026-11-11T16:05:00.000Z",
        "2026-11-11T15:30:00.000Z",
    ]


@respx.mock
async def test_recent_hits_applies_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    respx.get(EXPORT_URL).mock(side_effect=_respond)
    get_recent_hits = await _recent(monkeypatch)
    result = await get_recent_hits(hostname="example.com", limit=1)
    assert result["count"] == 3
    assert len(result["hits"]) == 1


async def test_recent_hits_rejects_bad_type(monkeypatch: pytest.MonkeyPatch) -> None:
    get_recent_hits = await _recent(monkeypatch)
    with pytest.raises(ValueError, match="type"):
        await get_recent_hits(hostname="example.com", type="sessions")


async def test_recent_hits_rejects_bad_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    get_recent_hits = await _recent(monkeypatch)
    with pytest.raises(ValueError, match="limit"):
        await get_recent_hits(hostname="example.com", limit=0)
