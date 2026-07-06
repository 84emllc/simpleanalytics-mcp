"""Tests for the list_websites tool."""

import httpx
import respx
from mcp.server.fastmcp import FastMCP

from simpleanalytics_mcp.tools.websites import register_websites_tools


def _get_tool(mcp: FastMCP, name: str):
    return mcp._tool_manager._tools[name].fn


@respx.mock
async def test_list_websites_calls_api() -> None:
    respx.get("https://simpleanalytics.com/api/websites").mock(
        return_value=httpx.Response(200, json=[{"hostname": "example.com"}])
    )
    mcp = FastMCP("test")
    register_websites_tools(mcp)
    list_websites = _get_tool(mcp, "list_websites")
    result = await list_websites()
    assert result == [{"hostname": "example.com"}]
