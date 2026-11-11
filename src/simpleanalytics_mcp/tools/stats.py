"""Aggregated statistics tool (Stats API) for SimpleAnalytics MCP."""

import asyncio
from typing import Any

from fastmcp import FastMCP

from simpleanalytics_mcp.client import default_timezone, get_json
from simpleanalytics_mcp.validation import metadata_params, parse_fields, previous_period

_COMPARED_TOTALS = ("pageviews", "visitors", "seconds_on_page")


def percent_change(current: Any, previous: Any) -> float | None:
    """Percent change from previous to current, or None when it is undefined."""
    if not isinstance(current, int | float) or not isinstance(previous, int | float):
        return None
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _event_totals(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    events = data.get("events")
    if not isinstance(events, list):
        return {}
    return {
        e["name"]: e.get("total", 0)
        for e in events
        if isinstance(e, dict) and "name" in e
    }


def compare_change(current: Any, previous: Any) -> dict[str, Any]:
    """Percent change for the compared totals and for each event name."""
    cur = current if isinstance(current, dict) else {}
    prev = previous if isinstance(previous, dict) else {}
    change: dict[str, Any] = {
        key: percent_change(cur.get(key), prev.get(key))
        for key in _COMPARED_TOTALS
        if key in cur or key in prev
    }
    cur_events = _event_totals(current)
    prev_events = _event_totals(previous)
    if cur_events or prev_events:
        names = list(cur_events) + [n for n in prev_events if n not in cur_events]
        change["events"] = {
            name: percent_change(cur_events.get(name, 0), prev_events.get(name))
            for name in names
        }
    return change


def register_stats_tools(mcp: FastMCP) -> None:
    """Register the Stats API tool with the MCP server."""

    @mcp.tool()
    async def get_stats(
        hostname: str,
        fields: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        interval: str | None = None,
        limit: int | None = None,
        events: list[str] | None = None,
        timezone: str | None = None,
        page: str | None = None,
        pages: list[str] | None = None,
        country: str | None = None,
        referrer: str | None = None,
        utm_source: str | None = None,
        utm_medium: str | None = None,
        utm_campaign: str | None = None,
        utm_content: str | None = None,
        utm_term: str | None = None,
        browser_name: str | None = None,
        os_name: str | None = None,
        device_type: str | None = None,
        metadata: dict[str, str] | None = None,
        compare: bool = False,
    ) -> Any:
        """
        Get dashboard-accurate aggregated statistics from SimpleAnalytics.

        fields (default ["pageviews", "visitors"]) chooses what to return:
        pageviews, visitors, histogram, pages, countries, referrers,
        utm_sources, utm_mediums, utm_campaigns, utm_contents, utm_terms,
        browser_names, os_names, device_types, seconds_on_page.

        start/end accept YYYY-MM-DD or relative keywords (yesterday, today);
        they default on the API side to one month ago / today. end is
        inclusive, even though the response's own "end" field shows the
        previous day. interval controls histogram granularity (hour, day,
        week, month, year). limit is 1-1000.

        events returns per-event totals for the listed names, or every event
        (up to 1000) with ["*"]. Event totals respect the filters below.

        Filters narrow the data and support trailing-* wildcards: page, pages
        (e.g. ["/blog/*"]), country, referrer, utm_source, utm_medium,
        utm_campaign, utm_content, utm_term, browser_name, os_name, device_type.
        metadata filters by metadata values, e.g. {"plan": "pro"}: exact match,
        all keys must match, up to 20 keys.

        compare also fetches the equal-length period ending the day before
        start (needs start and end as YYYY-MM-DD) and returns current,
        previous, previous_start, previous_end, and change_percent for
        pageviews, visitors, seconds_on_page, and each event. A change is
        null when the previous value is 0 or missing.
        """
        params: dict[str, Any] = {
            "fields": parse_fields(fields if fields else ["pageviews", "visitors"]),
            "timezone": timezone or default_timezone(),
        }
        if interval is not None:
            params["interval"] = interval
        if limit is not None:
            params["limit"] = limit
        if events:
            params["events"] = ",".join(events)
        if page is not None:
            params["page"] = page
        if pages:
            params["pages"] = ",".join(pages)
        if country is not None:
            params["country"] = country
        if referrer is not None:
            params["referrer"] = referrer
        if utm_source is not None:
            params["utm_source"] = utm_source
        if utm_medium is not None:
            params["utm_medium"] = utm_medium
        if utm_campaign is not None:
            params["utm_campaign"] = utm_campaign
        if utm_content is not None:
            params["utm_content"] = utm_content
        if utm_term is not None:
            params["utm_term"] = utm_term
        if browser_name is not None:
            params["browser_name"] = browser_name
        if os_name is not None:
            params["os_name"] = os_name
        if device_type is not None:
            params["device_type"] = device_type
        if metadata:
            params.update(metadata_params(metadata))

        path = f"/{hostname}.json"

        if not compare:
            if start is not None:
                params["start"] = start
            if end is not None:
                params["end"] = end
            return await get_json(path, params, need_user_id=False)

        if start is None or end is None:
            raise ValueError("compare needs start and end as YYYY-MM-DD dates")
        prev_start, prev_end = previous_period(start, end)
        current, previous = await asyncio.gather(
            get_json(path, {**params, "start": start, "end": end}, need_user_id=False),
            get_json(path, {**params, "start": prev_start, "end": prev_end}, need_user_id=False),
        )
        return {
            "current": current,
            "previous": previous,
            "previous_start": prev_start,
            "previous_end": prev_end,
            "change_percent": compare_change(current, previous),
        }
