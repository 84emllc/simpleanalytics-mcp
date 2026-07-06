"""Raw datapoint export tool (Export API) for SimpleAnalytics MCP."""

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from simpleanalytics_mcp.client import default_timezone, get_json
from simpleanalytics_mcp.validation import parse_fields, validate_export_range

_DEFAULT_FIELDS = ["added_iso", "path", "country_code", "device_type"]


def _export_dir() -> Path:
    """Directory where large exports are written (SA_EXPORT_DIR or system temp)."""
    return Path(os.environ.get("SA_EXPORT_DIR") or tempfile.gettempdir())


def _inline_limit() -> int:
    """Max rows returned inline before switching to file output."""
    return int(os.environ.get("SA_INLINE_ROW_LIMIT", "500"))


def write_export_file(
    rows: list[Any],
    hostname: str,
    start: str,
    end: str,
    timestamp: str,
    export_dir: Path,
) -> Path:
    """Write rows to a newline-delimited JSON file and return its path."""
    safe_host = hostname.replace("/", "_")
    filename = f"{safe_host}-{start}_{end}-{timestamp}.ndjson"
    path = Path(export_dir) / filename
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    return path


def register_export_tools(mcp: FastMCP) -> None:
    """Register the Export API tool with the MCP server."""

    @mcp.tool()
    async def export_datapoints(
        hostname: str,
        start: str,
        end: str,
        fields: list[str] | None = None,
        robots: bool = False,
        type: str = "pageviews",
        timezone: str | None = None,
    ) -> dict[str, Any]:
        """
        Export raw SimpleAnalytics datapoints (one row per page view or event).

        fields is an arbitrary passthrough list (default
        ["added_iso", "path", "country_code", "device_type"]); it accepts any
        field name, including metadata.* and undocumented fields such as
        datapoint and session_id.

        start/end use YYYY-MM-DD, or hourly YYYY-MM-DDTHH (both must include the
        hour and share the same day). robots includes robot traffic when True.

        Small results (<= SA_INLINE_ROW_LIMIT, default 500) are returned inline
        under "rows". Larger results are written to a newline-delimited JSON file
        and the response returns row_count, file_path, and a sample_head.
        """
        validate_export_range(start, end)
        field_list = fields if fields else list(_DEFAULT_FIELDS)
        params: dict[str, Any] = {
            "format": "json",
            "hostname": hostname,
            "start": start,
            "end": end,
            "fields": parse_fields(field_list),
            "robots": str(robots).lower(),
            "type": type,
            "timezone": timezone or default_timezone(),
        }

        data = await get_json("/api/export/datapoints", params, need_user_id=True)
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = data.get("data", [])
        else:
            rows = []

        row_count = len(rows)
        if row_count <= _inline_limit():
            return {
                "row_count": row_count,
                "fields": field_list,
                "inline": True,
                "rows": rows,
            }

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = write_export_file(rows, hostname, start, end, timestamp, _export_dir())
        return {
            "row_count": row_count,
            "fields": field_list,
            "inline": False,
            "file_path": str(path),
            "sample_head": rows[:10],
        }
