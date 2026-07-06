"""Tests for the list_websites tool."""

import httpx
import respx
from fastmcp import FastMCP

from simpleanalytics_mcp.tools.websites import register_websites_tools


async def _get_tool(mcp: FastMCP, name: str):
    return (await mcp.get_tool(name)).fn


@respx.mock
async def test_list_websites_calls_api() -> None:
    respx.get("https://simpleanalytics.com/api/websites").mock(
        return_value=httpx.Response(200, json=[{"hostname": "example.com"}])
    )
    mcp = FastMCP("test")
    register_websites_tools(mcp)
    list_websites = await _get_tool(mcp, "list_websites")
    result = await list_websites()
    assert result == [{"hostname": "example.com"}]
