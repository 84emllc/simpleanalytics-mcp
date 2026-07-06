"""Tests for the export_datapoints tool."""

import json
from pathlib import Path

import httpx
import pytest
import respx
from fastmcp import FastMCP

from simpleanalytics_mcp.tools.export import register_export_tools, write_export_file


async def _get_tool(mcp: FastMCP, name: str):
    return (await mcp.get_tool(name)).fn


async def _export():
    mcp = FastMCP("test")
    register_export_tools(mcp)
    return await _get_tool(mcp, "export_datapoints")


def _rows(n: int) -> list[dict[str, str]]:
    return [{"path": f"/p{i}", "added_iso": "2026-06-24T00:00:00Z"} for i in range(n)]


@respx.mock
async def test_export_inline_when_small() -> None:
    route = respx.get("https://simpleanalytics.com/api/export/datapoints").mock(
        return_value=httpx.Response(200, json=_rows(3))
    )
    export_datapoints = await _export()
    result = await export_datapoints(
        hostname="example.com", start="2026-06-01", end="2026-06-30"
    )
    assert result["inline"] is True
    assert result["row_count"] == 3
    assert len(result["rows"]) == 3
    params = route.calls.last.request.url.params
    assert params["format"] == "json"
    assert params["hostname"] == "example.com"
    assert params["robots"] == "false"
    assert params["type"] == "pageviews"
    assert params["fields"] == "added_iso,path,country_code,device_type"


@respx.mock
async def test_export_writes_file_when_large(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SA_EXPORT_DIR", str(tmp_path))
    monkeypatch.setenv("SA_INLINE_ROW_LIMIT", "5")
    respx.get("https://simpleanalytics.com/api/export/datapoints").mock(
        return_value=httpx.Response(200, json=_rows(9))
    )
    export_datapoints = await _export()
    result = await export_datapoints(
        hostname="example.com", start="2026-06-01", end="2026-06-30"
    )
    assert result["inline"] is False
    assert result["row_count"] == 9
    assert len(result["sample_head"]) == 9  # <= 10 returned in full
    written = Path(result["file_path"])
    assert written.exists()
    lines = written.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 9
    assert json.loads(lines[0])["path"] == "/p0"


async def test_export_rejects_mixed_hourly_range() -> None:
    export_datapoints = await _export()
    with pytest.raises(ValueError, match="both"):
        await export_datapoints(
            hostname="example.com", start="2026-06-24T09", end="2026-06-24"
        )


def test_write_export_file_names_and_content(tmp_path: Path) -> None:
    path = write_export_file(
        _rows(2), "sub.example.com", "2026-06-01", "2026-06-30", "20260706T120000Z", tmp_path
    )
    assert path.parent == tmp_path
    assert path.name == "sub.example.com-2026-06-01_2026-06-30-20260706T120000Z.ndjson"
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
