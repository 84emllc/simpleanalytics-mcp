"""SimpleAnalytics MCP server entry point."""

from fastmcp import FastMCP


def create_server() -> FastMCP:
    """Create and configure the SimpleAnalytics MCP server."""
    mcp = FastMCP(
        "SimpleAnalytics MCP",
        instructions=(
            "MCP server for SimpleAnalytics. Use get_stats for dashboard-accurate "
            "aggregates (pageviews, visitors, top pages, referrers, UTMs, countries, "
            "devices, histograms, event counts), export_datapoints for raw row-level "
            "data, and list_websites to discover hostnames. Requires SA_API_KEY and "
            "SA_USER_ID environment variables."
        ),
    )
    return mcp


mcp = create_server()


def main() -> None:
    """CLI entry point."""
    mcp.run()


if __name__ == "__main__":
    main()
