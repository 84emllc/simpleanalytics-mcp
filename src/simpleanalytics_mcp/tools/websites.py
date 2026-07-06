"""Website discovery tool for SimpleAnalytics MCP."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from simpleanalytics_mcp.client import get_json


def register_websites_tools(mcp: FastMCP) -> None:
    """Register website discovery tools with the MCP server."""

    @mcp.tool()
    async def list_websites() -> Any:
        """
        List the websites/hostnames in the SimpleAnalytics account.

        Use this to discover which hostnames can be passed to get_stats and
        export_datapoints. Requires SA_API_KEY and SA_USER_ID.
        """
        return await get_json("/api/websites", {}, need_user_id=True)
