"""Tests for server construction."""

from fastmcp import FastMCP

from simpleanalytics_mcp.server import create_server


def test_create_server_returns_fastmcp() -> None:
    server = create_server()
    assert isinstance(server, FastMCP)


async def test_list_websites_registered() -> None:
    server = create_server()
    assert await server.get_tool("list_websites") is not None
