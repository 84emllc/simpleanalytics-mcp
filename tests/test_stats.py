"""Tests for the get_stats tool."""

import httpx
import pytest
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


@respx.mock
async def test_get_stats_passes_metadata_filters() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={})
    )
    get_stats = await _stats()
    await get_stats(hostname="example.com", metadata={"plan": "pro"})
    params = route.calls.last.request.url.params
    assert params["metadata.plan"] == "pro"


async def test_get_stats_rejects_bad_metadata_key() -> None:
    get_stats = await _stats()
    with pytest.raises(ValueError, match="metadata key"):
        await get_stats(hostname="example.com", metadata={"bad key": "x"})


@respx.mock
async def test_get_stats_compare_fetches_previous_period() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.params["start"] == "2026-11-01":
            return httpx.Response(
                200,
                json={
                    "pageviews": 150,
                    "visitors": 100,
                    "seconds_on_page": 20,
                    "events": [{"name": "signup", "total": 6}, {"name": "new", "total": 2}],
                },
            )
        return httpx.Response(
            200,
            json={
                "pageviews": 100,
                "visitors": 100,
                "seconds_on_page": 0,
                "events": [{"name": "signup", "total": 4}, {"name": "gone", "total": 1}],
            },
        )

    route = respx.get("https://simpleanalytics.com/example.com.json").mock(side_effect=respond)
    get_stats = await _stats()
    result = await get_stats(
        hostname="example.com",
        start="2026-11-01",
        end="2026-11-10",
        events=["*"],
        compare=True,
    )
    starts = sorted(call.request.url.params["start"] for call in route.calls)
    ends = sorted(call.request.url.params["end"] for call in route.calls)
    assert starts == ["2026-10-22", "2026-11-01"]
    assert ends == ["2026-10-31", "2026-11-10"]
    assert result["previous_start"] == "2026-10-22"
    assert result["previous_end"] == "2026-10-31"
    assert result["current"]["pageviews"] == 150
    assert result["previous"]["pageviews"] == 100
    assert result["change_percent"]["pageviews"] == 50.0
    assert result["change_percent"]["visitors"] == 0.0
    assert result["change_percent"]["seconds_on_page"] is None
    assert result["change_percent"]["events"] == {"signup": 50.0, "new": None, "gone": -100.0}


async def test_get_stats_compare_requires_explicit_dates() -> None:
    get_stats = await _stats()
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        await get_stats(hostname="example.com", compare=True)
