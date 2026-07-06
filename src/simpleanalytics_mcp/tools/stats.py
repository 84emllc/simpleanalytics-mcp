"""Aggregated statistics tool (Stats API) for SimpleAnalytics MCP."""

from typing import Any

from fastmcp import FastMCP

from simpleanalytics_mcp.client import default_timezone, get_json
from simpleanalytics_mcp.validation import parse_fields


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
    ) -> Any:
        """
        Get dashboard-accurate aggregated statistics from SimpleAnalytics.

        fields (default ["pageviews", "visitors"]) chooses what to return:
        pageviews, visitors, histogram, pages, countries, referrers,
        utm_sources, utm_mediums, utm_campaigns, utm_contents, utm_terms,
        browser_names, os_names, device_types, seconds_on_page.

        start/end accept YYYY-MM-DD or relative keywords (yesterday, today);
        they default on the API side to one month ago / today. interval controls
        histogram granularity (hour, day, week, month, year). limit is 1-1000.
        events counts specific event names (independent of filters).

        Filters narrow the data and support trailing-* wildcards: page, pages
        (e.g. ["/blog/*"]), country, referrer, utm_source, utm_medium,
        utm_campaign, utm_content, utm_term, browser_name, os_name, device_type.
        """
        params: dict[str, Any] = {
            "fields": parse_fields(fields if fields else ["pageviews", "visitors"]),
            "timezone": timezone or default_timezone(),
        }
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
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

        return await get_json(f"/{hostname}.json", params, need_user_id=False)
