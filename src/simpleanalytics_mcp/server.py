"""SimpleAnalytics MCP server entry point."""

from fastmcp import FastMCP

from simpleanalytics_mcp.tools.events import register_events_tools
from simpleanalytics_mcp.tools.export import register_export_tools
from simpleanalytics_mcp.tools.recent import register_recent_tools
from simpleanalytics_mcp.tools.stats import register_stats_tools
from simpleanalytics_mcp.tools.websites import register_websites_tools


def create_server() -> FastMCP:
    """Create and configure the SimpleAnalytics MCP server."""
    mcp = FastMCP(
        "SimpleAnalytics MCP",
        instructions=(
            "MCP server for SimpleAnalytics. Use get_stats for dashboard-accurate "
            "aggregates (pageviews, visitors, top pages, referrers, UTMs, countries, "
            "devices, histograms, event counts), with metadata filters and compare "
            "for the previous period; get_event_histogram for one event over time; "
            "get_recent_hits for the last 60 minutes of raw hits; export_datapoints "
            "for raw row-level data; and list_websites to discover hostnames. "
            "Requires SA_API_KEY and SA_USER_ID environment variables."
        ),
    )
    register_websites_tools(mcp)
    register_stats_tools(mcp)
    register_export_tools(mcp)
    register_events_tools(mcp)
    register_recent_tools(mcp)

    return mcp


mcp = create_server()


def main() -> None:
    """CLI entry point."""
    mcp.run()


if __name__ == "__main__":
    main()
