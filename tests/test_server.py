"""Tests for server construction."""

from mcp.server.fastmcp import FastMCP

from simpleanalytics_mcp.server import create_server


def test_create_server_returns_fastmcp() -> None:
    server = create_server()
    assert isinstance(server, FastMCP)


def test_list_websites_registered() -> None:
    server = create_server()
    assert "list_websites" in server._tool_manager._tools
