"""Tests for the get_stats tool."""

import httpx
import respx
from fastmcp import FastMCP

from simpleanalytics_mcp.tools.stats import register_stats_tools


async def _get_tool(mcp: FastMCP, name: str):
    return (await mcp.get_tool(name)).fn


async def _stats():
    mcp = FastMCP("test")
    register_stats_tools(mcp)
    return await _get_tool(mcp, "get_stats")


@respx.mock
async def test_get_stats_defaults() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={"pageviews": 10, "visitors": 7})
    )
    get_stats = await _stats()
    result = await get_stats(hostname="example.com")
    assert result == {"pageviews": 10, "visitors": 7}
    params = route.calls.last.request.url.params
    assert params["fields"] == "pageviews,visitors"
    assert params["version"] == "6"
    assert params["timezone"] == "America/Chicago"


@respx.mock
async def test_get_stats_passes_filters_and_lists() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={})
    )
    get_stats = await _stats()
    await get_stats(
        hostname="example.com",
        fields=["pages", "referrers"],
        start="2026-06-01",
        end="2026-06-30",
        interval="day",
        limit=100,
        events=["signup", "purchase"],
        pages=["/blog/*", "/contact"],
        country="US",
        device_type="mobile",
    )
    params = route.calls.last.request.url.params
    assert params["fields"] == "pages,referrers"
    assert params["start"] == "2026-06-01"
    assert params["end"] == "2026-06-30"
    assert params["interval"] == "day"
    assert params["limit"] == "100"
    assert params["events"] == "signup,purchase"
    assert params["pages"] == "/blog/*,/contact"
    assert params["country"] == "US"
    assert params["device_type"] == "mobile"


@respx.mock
async def test_get_stats_omits_unset_params() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={})
    )
    get_stats = await _stats()
    await get_stats(hostname="example.com")
    params = route.calls.last.request.url.params
    assert "country" not in params
    assert "interval" not in params
    assert "events" not in params
