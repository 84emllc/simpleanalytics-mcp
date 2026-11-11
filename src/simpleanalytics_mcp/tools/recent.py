"""Recent hits tool for SimpleAnalytics MCP, built on hourly Export API pulls."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from simpleanalytics_mcp.client import default_timezone
from simpleanalytics_mcp.tools.export import fetch_datapoints

_TYPES = ("all", "pageviews", "events")
_MAX_LIMIT = 100

_FIELDS = [
    "added_iso",
    "datapoint",
    "path",
    "referrer_hostname",
    "country_code",
    "device_type",
    "browser_name",
    "os_name",
    "is_robot",
]


def utc_now() -> datetime:
    """Current time in UTC."""
    return datetime.now(UTC)


def register_recent_tools(mcp: FastMCP) -> None:
    """Register the recent hits tool with the MCP server."""

    @mcp.tool()
    async def get_recent_hits(
        hostname: str,
        type: str = "all",
        limit: int = 25,
        robots: bool = True,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        """
        Get the page views and events of the last 60 minutes, newest first.

        Use it to check that the script sends data. It exports the current
        and previous hour in hourly mode and keeps hits from the last 60
        minutes. type is all, pageviews, or events. limit is 1-100. robots
        (default True) includes robot traffic, which shows as is_robot.
        count is the number of hits in the window before limit is applied.
        """
        if type not in _TYPES:
            raise ValueError(f"type must be one of {', '.join(_TYPES)}, got {type!r}")
        if not 1 <= limit <= _MAX_LIMIT:
            raise ValueError(f"limit must be between 1 and {_MAX_LIMIT}, got {limit}")
        tz_name = timezone or default_timezone()
        tz = ZoneInfo(tz_name)

        now = utc_now()
        since = now - timedelta(minutes=60)
        hours = sorted({moment.astimezone(tz).strftime("%Y-%m-%dT%H") for moment in (since, now)})

        batches = await asyncio.gather(
            *(
                fetch_datapoints(
                    hostname,
                    hour,
                    hour,
                    _FIELDS,
                    type=type,
                    robots=robots,
                    timezone=tz_name,
                )
                for hour in hours
            )
        )

        hits: list[tuple[datetime, dict[str, Any]]] = []
        for rows in batches:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                added = row.get("added_iso")
                if not isinstance(added, str):
                    continue
                moment = datetime.fromisoformat(added)
                if moment >= since:
                    hits.append((moment, row))
        hits.sort(key=lambda item: item[0], reverse=True)

        return {
            "hostname": hostname,
            "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timezone": tz_name,
            "count": len(hits),
            "hits": [row for _, row in hits[:limit]],
        }
