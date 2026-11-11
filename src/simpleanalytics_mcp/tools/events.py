"""Per-event histogram tool for SimpleAnalytics MCP, built on the Export API."""

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from simpleanalytics_mcp.client import default_timezone
from simpleanalytics_mcp.tools.export import fetch_datapoints
from simpleanalytics_mcp.validation import parse_day_range

INTERVALS = ("hour", "day", "week", "month", "year")

_EXPORT_FIELDS = [
    "added_iso",
    "datapoint",
    "path",
    "referrer_hostname",
    "country_code",
    "device_type",
    "browser_name",
    "os_name",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
]


def bucket_key(moment: datetime, interval: str) -> str:
    """Histogram bucket label for a local datetime."""
    if interval == "hour":
        return moment.strftime("%Y-%m-%dT%H")
    if interval == "day":
        return moment.date().isoformat()
    if interval == "week":
        return (moment.date() - timedelta(days=moment.weekday())).isoformat()
    if interval == "month":
        return moment.strftime("%Y-%m")
    return moment.strftime("%Y")


def bucket_keys(start: date, end: date, interval: str) -> list[str]:
    """Ordered, de-duplicated bucket labels covering start..end inclusive."""
    keys: list[str] = []
    day = start
    while day <= end:
        hours = range(24) if interval == "hour" else range(1)
        for hour in hours:
            key = bucket_key(datetime(day.year, day.month, day.day, hour), interval)
            if not keys or keys[-1] != key:
                keys.append(key)
        day += timedelta(days=1)
    return keys


def _matches(row: dict[str, Any], filters: dict[str, str]) -> bool:
    for field, wanted in filters.items():
        value = row.get(field)
        if not isinstance(value, str):
            return False
        if field == "path" and wanted.endswith("*"):
            if not value.startswith(wanted[:-1]):
                return False
        elif field == "country_code":
            if value.upper() != wanted.upper():
                return False
        elif value != wanted:
            return False
    return True


def register_events_tools(mcp: FastMCP) -> None:
    """Register the event histogram tool with the MCP server."""

    @mcp.tool()
    async def get_event_histogram(
        hostname: str,
        event: str,
        start: str,
        end: str,
        interval: str = "day",
        timezone: str | None = None,
        page: str | None = None,
        country: str | None = None,
        referrer: str | None = None,
        device_type: str | None = None,
        browser_name: str | None = None,
        os_name: str | None = None,
        utm_source: str | None = None,
        utm_medium: str | None = None,
        utm_campaign: str | None = None,
        utm_content: str | None = None,
        utm_term: str | None = None,
        robots: bool = False,
    ) -> dict[str, Any]:
        """
        Get how often one event happened per hour, day, week, month, or year.

        For event totals (every event, or several at once), use get_stats with
        events=["*"] instead: it is one cheap Stats API call and supports
        compare. This tool exports the raw events and counts them, so it can
        bucket a single event over time.

        start/end are inclusive YYYY-MM-DD dates in the timezone (default
        SA_DEFAULT_TIMEZONE). interval is hour, day, week (buckets start on
        Monday), month, or year. Every bucket in the range is returned, with 0
        for buckets without the event.

        Filters match the exported row values: page (path, trailing * for a
        prefix), country (ISO code), referrer (the normalized referrer
        hostname the Export API stores, e.g. "google" not "google.com"),
        device_type, browser_name, os_name, utm_source, utm_medium,
        utm_campaign, utm_content, utm_term. robots includes robot traffic.
        """
        if interval not in INTERVALS:
            raise ValueError(f"interval must be one of {', '.join(INTERVALS)}, got {interval!r}")
        start_d, end_d = parse_day_range(start, end)
        tz_name = timezone or default_timezone()
        tz = ZoneInfo(tz_name)

        candidates = {
            "path": page,
            "country_code": country,
            "referrer_hostname": referrer,
            "device_type": device_type,
            "browser_name": browser_name,
            "os_name": os_name,
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign,
            "utm_content": utm_content,
            "utm_term": utm_term,
        }
        filters = {field: value for field, value in candidates.items() if value is not None}

        rows = await fetch_datapoints(
            hostname,
            start,
            end,
            _EXPORT_FIELDS,
            type="events",
            robots=robots,
            timezone=tz_name,
        )

        counts = dict.fromkeys(bucket_keys(start_d, end_d, interval), 0)
        for row in rows:
            if not isinstance(row, dict) or row.get("datapoint") != event:
                continue
            if not _matches(row, filters):
                continue
            added = row.get("added_iso")
            if not isinstance(added, str):
                continue
            local = datetime.fromisoformat(added).astimezone(tz)
            key = bucket_key(local, interval)
            if key in counts:
                counts[key] += 1

        return {
            "hostname": hostname,
            "event": event,
            "start": start,
            "end": end,
            "interval": interval,
            "timezone": tz_name,
            "total": sum(counts.values()),
            "histogram": [{"bucket": key, "count": n} for key, n in counts.items()],
        }
