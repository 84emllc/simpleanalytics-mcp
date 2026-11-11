"""Tests for the get_event_histogram tool."""

from datetime import date

import httpx
import pytest
import respx
from fastmcp import FastMCP

from simpleanalytics_mcp.tools.events import bucket_keys, register_events_tools

EXPORT_URL = "https://simpleanalytics.com/api/export/datapoints"


async def _histogram():
    mcp = FastMCP("test")
    register_events_tools(mcp)
    return (await mcp.get_tool("get_event_histogram")).fn


def _row(added_iso: str, datapoint: str = "signup", **extra: str | None) -> dict[str, str | None]:
    row: dict[str, str | None] = {"added_iso": added_iso, "datapoint": datapoint, "path": "/"}
    row.update(extra)
    return row


def test_bucket_keys_day() -> None:
    assert bucket_keys(date(2026, 11, 9), date(2026, 11, 11), "day") == [
        "2026-11-09",
        "2026-11-10",
        "2026-11-11",
    ]


def test_bucket_keys_week_starts_monday() -> None:
    assert bucket_keys(date(2026, 11, 4), date(2026, 11, 17), "week") == [
        "2026-11-02",
        "2026-11-09",
        "2026-11-16",
    ]


def test_bucket_keys_month_and_year() -> None:
    assert bucket_keys(date(2026, 11, 20), date(2027, 1, 5), "month") == [
        "2026-11",
        "2026-12",
        "2027-01",
    ]
    assert bucket_keys(date(2026, 11, 20), date(2027, 1, 5), "year") == ["2026", "2027"]


def test_bucket_keys_hour() -> None:
    keys = bucket_keys(date(2026, 11, 10), date(2026, 11, 11), "hour")
    assert len(keys) == 48
    assert keys[0] == "2026-11-10T00"
    assert keys[-1] == "2026-11-11T23"


@respx.mock
async def test_histogram_counts_event_by_local_day() -> None:
    route = respx.get(EXPORT_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "datapoints": [
                    _row("2026-11-10T05:30:00.000Z"),
                    _row("2026-11-10T06:30:00.000Z"),
                    _row("2026-11-10T07:00:00.000Z", datapoint="other"),
                    _row("2026-11-11T20:00:00.000Z"),
                ]
            },
        )
    )
    get_event_histogram = await _histogram()
    result = await get_event_histogram(
        hostname="example.com", event="signup", start="2026-11-09", end="2026-11-11"
    )
    params = route.calls.last.request.url.params
    assert params["type"] == "events"
    assert params["timezone"] == "America/Chicago"
    assert result["total"] == 3
    assert result["histogram"] == [
        {"bucket": "2026-11-09", "count": 1},
        {"bucket": "2026-11-10", "count": 1},
        {"bucket": "2026-11-11", "count": 1},
    ]


@respx.mock
async def test_histogram_applies_filters() -> None:
    respx.get(EXPORT_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "datapoints": [
                    _row("2026-11-10T15:00:00Z", path="/blog/a", device_type="mobile",
                         country_code="US"),
                    _row("2026-11-10T15:00:00Z", path="/blog/b", device_type="desktop",
                         country_code="US"),
                    _row("2026-11-10T15:00:00Z", path="/contact", device_type="mobile",
                         country_code="US"),
                    _row("2026-11-10T15:00:00Z", path="/blog/c", device_type="mobile",
                         country_code="NL"),
                ]
            },
        )
    )
    get_event_histogram = await _histogram()
    result = await get_event_histogram(
        hostname="example.com",
        event="signup",
        start="2026-11-10",
        end="2026-11-10",
        page="/blog/*",
        device_type="mobile",
        country="us",
    )
    assert result["total"] == 1


async def test_histogram_rejects_bad_interval() -> None:
    get_event_histogram = await _histogram()
    with pytest.raises(ValueError, match="interval"):
        await get_event_histogram(
            hostname="example.com",
            event="signup",
            start="2026-11-10",
            end="2026-11-10",
            interval="minute",
        )


async def test_histogram_rejects_placeholder_dates() -> None:
    get_event_histogram = await _histogram()
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        await get_event_histogram(
            hostname="example.com", event="signup", start="today-30d", end="today"
        )
