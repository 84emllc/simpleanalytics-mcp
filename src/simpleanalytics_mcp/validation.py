"""Input validation helpers for SimpleAnalytics MCP tools."""

import re
from datetime import datetime

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HOUR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}$")


def validate_date(value: str, *, field: str) -> None:
    """Validate a date as YYYY-MM-DD or hourly YYYY-MM-DDTHH."""
    if _DATE_RE.match(value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"{field} is not a real date: {value!r}") from exc
        return
    if _HOUR_RE.match(value):
        try:
            datetime.strptime(value, "%Y-%m-%dT%H")
        except ValueError as exc:
            raise ValueError(f"{field} has an invalid date or hour: {value!r}") from exc
        return
    raise ValueError(
        f"{field} must be YYYY-MM-DD or hourly YYYY-MM-DDTHH, got {value!r}"
    )


def is_hourly(value: str) -> bool:
    """Return True when the value includes an hour component (YYYY-MM-DDTHH)."""
    return bool(_HOUR_RE.match(value))


def validate_export_range(start: str, end: str) -> None:
    """Validate an Export API date range and enforce hourly constraints."""
    validate_date(start, field="start")
    validate_date(end, field="end")
    start_hourly = is_hourly(start)
    end_hourly = is_hourly(end)
    if start_hourly != end_hourly:
        raise ValueError(
            "hourly export requires both start and end to include an hour "
            "(YYYY-MM-DDTHH)"
        )
    if start_hourly and start[:10] != end[:10]:
        raise ValueError(
            "hourly export must cover a single day: start and end dates must match"
        )


def parse_fields(fields: list[str]) -> str:
    """Trim and drop empty field tokens; return a comma-joined string.

    No documented-field whitelist is applied: arbitrary field names
    (including metadata.* and undocumented fields) pass through.
    """
    cleaned = [f.strip() for f in fields if f and f.strip()]
    if not cleaned:
        raise ValueError("fields must contain at least one non-empty field name")
    return ",".join(cleaned)
