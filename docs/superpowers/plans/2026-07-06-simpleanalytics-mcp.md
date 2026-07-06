# SimpleAnalytics MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python MCP server that gives agents access to SimpleAnalytics data (Stats API aggregates + Export API raw datapoints + website discovery) for SEO work joined with Google Search Console and other sources.

**Architecture:** FastMCP server, `src/` layout. A thin async httpx `client` owns transport, auth-header injection, version pinning, and error mapping. Pure `validation` functions guard inputs. Three tool modules (`stats`, `export`, `websites`) each register one tool via `register_*_tools(mcp)`. `server` wires them together. Mirrors the in-house `uptimerobot-mcp` layout.

**Tech Stack:** Python 3.12, fastmcp, httpx (async), python-dotenv, pytest + pytest-asyncio + respx (mocked HTTP), ruff, mypy (strict).

## Global Constraints

- Python: `requires-python = ">=3.12"`.
- Dependencies: `fastmcp>=3.0.0`, `httpx>=0.28.0`, `python-dotenv>=1.1.0`. Dev: `pytest>=8.0`, `pytest-asyncio>=0.24`, `respx>=0.21`, `ruff>=0.9.0`, `mypy>=1.14`.
- API version pinned to `6` (constant `API_VERSION = "6"`, sent as `version` on every request).
- Base URL: `https://simpleanalytics.com`.
- Auth: `Api-Key` header always; `User-Id` header for Export and list_websites.
- Credentials come only from the environment / `.env` (via python-dotenv). Never read from arbitrary files.
- Env vars: `SA_API_KEY` (required), `SA_USER_ID` (required for Export + list_websites), `SA_DEFAULT_TIMEZONE` (default `America/Chicago`), `SA_EXPORT_DIR` (default system temp dir), `SA_INLINE_ROW_LIMIT` (default `500`).
- `fields` is an arbitrary passthrough list — NO documented-field whitelist (must allow `metadata.*`, `datapoint`, `session_id`). Validate only that tokens are non-empty.
- Tests never hit the live API; all HTTP is mocked with respx. One optional live smoke test is gated behind an env var and skipped by default.
- ruff: `target-version = "py312"`, `line-length = 100`, lint select `["E","F","I","UP","B","SIM"]`. mypy: `strict = true`.
- License MIT, author "84EM" <hello@84em.com>. 84EM always uppercase. No emojis or Claude attribution in commits.

---

### Task 1: Project scaffold + minimal server

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/simpleanalytics_mcp/__init__.py`
- Create: `src/simpleanalytics_mcp/__main__.py`
- Create: `src/simpleanalytics_mcp/server.py`
- Create: `src/simpleanalytics_mcp/tools/__init__.py`
- Test: `tests/__init__.py`
- Test: `tests/conftest.py`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `create_server() -> FastMCP` and `main() -> None` in `server.py`; module `simpleanalytics_mcp` importable; `python -m simpleanalytics_mcp` runs the server. Tool-registration functions are added in later tasks and called inside `create_server()`.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "simpleanalytics-mcp"
version = "0.1.0"
description = "MCP server for SimpleAnalytics Stats and Export APIs"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.12"
authors = [{ name = "84EM", email = "hello@84em.com" }]
keywords = ["mcp", "simpleanalytics", "analytics", "seo", "model-context-protocol"]
dependencies = [
    "fastmcp>=3.0.0",
    "httpx>=0.28.0",
    "python-dotenv>=1.1.0",
]

[project.scripts]
simpleanalytics-mcp = "simpleanalytics_mcp.server:main"

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
include = ["simpleanalytics_mcp*"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "respx>=0.21",
    "ruff>=0.9.0",
    "mypy>=1.14",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `.gitignore`**

```gitignore
__pycache__/
*.py[cod]
.venv/
.env
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/
dist/
build/
```

- [ ] **Step 3: Create package init files**

`src/simpleanalytics_mcp/__init__.py`:

```python
"""SimpleAnalytics MCP server."""

__version__ = "0.1.0"
```

`src/simpleanalytics_mcp/tools/__init__.py`:

```python
"""SimpleAnalytics MCP tools."""
```

`src/simpleanalytics_mcp/__main__.py`:

```python
"""Enable `python -m simpleanalytics_mcp`."""

from simpleanalytics_mcp.server import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create `src/simpleanalytics_mcp/server.py`**

```python
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
```

- [ ] **Step 5: Create test scaffolding**

`tests/__init__.py`:

```python
```

`tests/conftest.py`:

```python
"""Shared pytest fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _sa_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide dummy SimpleAnalytics credentials for all tests."""
    monkeypatch.setenv("SA_API_KEY", "sa_api_key_test")
    monkeypatch.setenv("SA_USER_ID", "sa_user_id_test")
```

`tests/test_server.py`:

```python
"""Tests for server construction."""

from fastmcp import FastMCP

from simpleanalytics_mcp.server import create_server


def test_create_server_returns_fastmcp() -> None:
    server = create_server()
    assert isinstance(server, FastMCP)
```

- [ ] **Step 6: Install and run the test to verify it passes**

Run: `pip install -e ".[dev]" && pytest tests/test_server.py -v`
Expected: PASS (`test_create_server_returns_fastmcp`).

- [ ] **Step 7: Run ruff and mypy**

Run: `ruff check . && mypy src`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .gitignore src tests
git commit -m "feat: scaffold SimpleAnalytics MCP with minimal server"
```

---

### Task 2: Input validation

**Files:**
- Create: `src/simpleanalytics_mcp/validation.py`
- Test: `tests/test_validation.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `validate_date(value: str, *, field: str) -> None` — raises `ValueError` unless `value` is `YYYY-MM-DD` or `YYYY-MM-DDTHH`.
  - `is_hourly(value: str) -> bool` — True when `value` matches `YYYY-MM-DDTHH`.
  - `validate_export_range(start: str, end: str) -> None` — validates both dates and enforces the hourly rule (both hourly-or-neither; if hourly, same calendar day).
  - `parse_fields(fields: list[str]) -> str` — trims/drops empty tokens, raises `ValueError` if none remain, returns a comma-joined string.

- [ ] **Step 1: Write the failing tests**

`tests/test_validation.py`:

```python
"""Tests for input validation helpers."""

import pytest

from simpleanalytics_mcp.validation import (
    is_hourly,
    parse_fields,
    validate_date,
    validate_export_range,
)


def test_validate_date_accepts_plain_date() -> None:
    validate_date("2026-06-24", field="start")


def test_validate_date_accepts_hourly_date() -> None:
    validate_date("2026-06-24T15", field="start")


def test_validate_date_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="start"):
        validate_date("June 24", field="start")


def test_validate_date_rejects_impossible_date() -> None:
    with pytest.raises(ValueError):
        validate_date("2026-13-40", field="end")


def test_validate_date_rejects_bad_hour() -> None:
    with pytest.raises(ValueError):
        validate_date("2026-06-24T25", field="start")


def test_is_hourly() -> None:
    assert is_hourly("2026-06-24T15") is True
    assert is_hourly("2026-06-24") is False


def test_validate_export_range_plain_ok() -> None:
    validate_export_range("2026-05-01", "2026-06-01")


def test_validate_export_range_hourly_ok() -> None:
    validate_export_range("2026-06-24T09", "2026-06-24T17")


def test_validate_export_range_mixed_rejected() -> None:
    with pytest.raises(ValueError, match="both"):
        validate_export_range("2026-06-24T09", "2026-06-24")


def test_validate_export_range_hourly_different_days_rejected() -> None:
    with pytest.raises(ValueError, match="single day"):
        validate_export_range("2026-06-24T09", "2026-06-25T17")


def test_parse_fields_joins_and_trims() -> None:
    assert parse_fields([" added_iso ", "path", ""]) == "added_iso,path"


def test_parse_fields_allows_undocumented_and_metadata() -> None:
    assert parse_fields(["datapoint", "session_id", "metadata.plan_text"]) == (
        "datapoint,session_id,metadata.plan_text"
    )


def test_parse_fields_rejects_all_empty() -> None:
    with pytest.raises(ValueError, match="at least one"):
        parse_fields([" ", ""])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'simpleanalytics_mcp.validation'`.

- [ ] **Step 3: Write `src/simpleanalytics_mcp/validation.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validation.py -v`
Expected: PASS (all 13 tests).

- [ ] **Step 5: Run ruff and mypy**

Run: `ruff check . && mypy src`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/simpleanalytics_mcp/validation.py tests/test_validation.py
git commit -m "feat: add input validation for dates, hourly ranges, and fields"
```

---

### Task 3: HTTP client (auth, version pin, error mapping)

**Files:**
- Create: `src/simpleanalytics_mcp/client.py`
- Test: `tests/test_client.py`

**Interfaces:**
- Consumes: nothing (module-level env access).
- Produces:
  - Constants `SA_BASE = "https://simpleanalytics.com"`, `API_VERSION = "6"`.
  - `default_timezone() -> str` — returns `SA_DEFAULT_TIMEZONE` or `"America/Chicago"`.
  - `async def get_json(path: str, params: dict[str, Any], *, need_user_id: bool) -> Any` — GETs `SA_BASE + path` with `version` injected, `Api-Key` header always, `User-Id` header when `need_user_id`, `raise_for_status`, returns parsed JSON. Maps non-2xx and transport errors to `ValueError`.

- [ ] **Step 1: Write the failing tests**

`tests/test_client.py`:

```python
"""Tests for the SimpleAnalytics HTTP client."""

import httpx
import pytest
import respx

from simpleanalytics_mcp.client import API_VERSION, default_timezone, get_json


@respx.mock
async def test_get_json_injects_version_and_api_key() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={"pageviews": 5})
    )
    result = await get_json("/example.com.json", {"fields": "pageviews"}, need_user_id=False)
    assert result == {"pageviews": 5}
    request = route.calls.last.request
    assert request.url.params["version"] == API_VERSION
    assert request.url.params["fields"] == "pageviews"
    assert request.headers["Api-Key"] == "sa_api_key_test"
    assert "User-Id" not in request.headers


@respx.mock
async def test_get_json_sends_user_id_when_required() -> None:
    route = respx.get("https://simpleanalytics.com/api/websites").mock(
        return_value=httpx.Response(200, json=[])
    )
    await get_json("/api/websites", {}, need_user_id=True)
    request = route.calls.last.request
    assert request.headers["User-Id"] == "sa_user_id_test"


@respx.mock
async def test_get_json_maps_auth_error() -> None:
    respx.get("https://simpleanalytics.com/api/websites").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )
    with pytest.raises(ValueError, match="SA_API_KEY"):
        await get_json("/api/websites", {}, need_user_id=True)


@respx.mock
async def test_get_json_maps_generic_error() -> None:
    respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(400, text="bad param")
    )
    with pytest.raises(ValueError, match="400"):
        await get_json("/example.com.json", {}, need_user_id=False)


@respx.mock
async def test_get_json_maps_transport_error() -> None:
    respx.get("https://simpleanalytics.com/api/websites").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(ValueError, match="request failed"):
        await get_json("/api/websites", {}, need_user_id=True)


def test_default_timezone_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SA_DEFAULT_TIMEZONE", "Europe/Amsterdam")
    assert default_timezone() == "Europe/Amsterdam"


def test_default_timezone_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SA_DEFAULT_TIMEZONE", raising=False)
    assert default_timezone() == "America/Chicago"


def test_get_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from simpleanalytics_mcp.client import _get_api_key

    monkeypatch.delenv("SA_API_KEY", raising=False)
    with pytest.raises(ValueError, match="SA_API_KEY"):
        _get_api_key()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'simpleanalytics_mcp.client'`.

- [ ] **Step 3: Write `src/simpleanalytics_mcp/client.py`**

```python
"""SimpleAnalytics API async HTTP client."""

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

SA_BASE = "https://simpleanalytics.com"
API_VERSION = "6"


def _get_api_key() -> str:
    key = os.environ.get("SA_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "SA_API_KEY environment variable is not set. "
            "Set it in your environment or in a .env file."
        )
    return key


def _get_user_id() -> str:
    user_id = os.environ.get("SA_USER_ID", "").strip()
    if not user_id:
        raise ValueError(
            "SA_USER_ID environment variable is not set. "
            "It is required for the Export API and list_websites."
        )
    return user_id


def default_timezone() -> str:
    """Return the configured default timezone (SA_DEFAULT_TIMEZONE)."""
    return os.environ.get("SA_DEFAULT_TIMEZONE", "America/Chicago")


async def get_json(path: str, params: dict[str, Any], *, need_user_id: bool) -> Any:
    """GET a SimpleAnalytics endpoint and return parsed JSON.

    Injects the pinned API version and the Api-Key header (plus User-Id when
    required). Maps non-2xx responses and transport errors to ValueError.
    """
    headers = {"Api-Key": _get_api_key()}
    if need_user_id:
        headers["User-Id"] = _get_user_id()

    query: dict[str, Any] = {"version": API_VERSION, **params}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{SA_BASE}{path}", params=query, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        detail = exc.response.text[:500]
        if status in (401, 403):
            raise ValueError(
                f"SimpleAnalytics auth failed ({status}). "
                f"Check SA_API_KEY and SA_USER_ID. {detail}"
            ) from exc
        raise ValueError(f"SimpleAnalytics API error {status}: {detail}") from exc
    except httpx.RequestError as exc:
        raise ValueError(f"SimpleAnalytics request failed: {exc}") from exc

    return response.json()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_client.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Run ruff and mypy**

Run: `ruff check . && mypy src`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/simpleanalytics_mcp/client.py tests/test_client.py
git commit -m "feat: add async HTTP client with auth, version pin, and error mapping"
```

---

### Task 4: `list_websites` tool

**Files:**
- Create: `src/simpleanalytics_mcp/tools/websites.py`
- Modify: `src/simpleanalytics_mcp/server.py`
- Test: `tests/test_websites.py`

**Interfaces:**
- Consumes: `get_json` from `client`.
- Produces: `register_websites_tools(mcp: FastMCP) -> None`, which registers an async tool `list_websites() -> Any` calling `GET /api/websites` with `need_user_id=True`.

- [ ] **Step 1: Write the failing test**

`tests/test_websites.py`:

```python
"""Tests for the list_websites tool."""

import httpx
import respx
from fastmcp import FastMCP

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_websites.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'simpleanalytics_mcp.tools.websites'`.

- [ ] **Step 3: Write `src/simpleanalytics_mcp/tools/websites.py`**

```python
"""Website discovery tool for SimpleAnalytics MCP."""

from typing import Any

from fastmcp import FastMCP

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
```

- [ ] **Step 4: Wire it into `server.py`**

Add the import near the top of `src/simpleanalytics_mcp/server.py`:

```python
from simpleanalytics_mcp.tools.websites import register_websites_tools
```

And call it inside `create_server()`, immediately before `return mcp`:

```python
    register_websites_tools(mcp)

    return mcp
```

- [ ] **Step 5: Add a registration test to `tests/test_server.py`**

Append to `tests/test_server.py`:

```python
def test_list_websites_registered() -> None:
    server = create_server()
    assert "list_websites" in server._tool_manager._tools
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_websites.py tests/test_server.py -v`
Expected: PASS.

- [ ] **Step 7: Run ruff and mypy**

Run: `ruff check . && mypy src`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add src/simpleanalytics_mcp/tools/websites.py src/simpleanalytics_mcp/server.py tests/test_websites.py tests/test_server.py
git commit -m "feat: add list_websites tool"
```

---

### Task 5: `get_stats` tool (Stats API)

**Files:**
- Create: `src/simpleanalytics_mcp/tools/stats.py`
- Modify: `src/simpleanalytics_mcp/server.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `get_json`, `default_timezone` from `client`; `parse_fields` from `validation`.
- Produces: `register_stats_tools(mcp: FastMCP) -> None`, registering async tool `get_stats(...) -> Any` that GETs `/{hostname}.json` with `need_user_id=False`.

Notes: Stats API `start`/`end` accept `YYYY-MM-DD` and relative keywords (`yesterday`, `today`), so they pass through unvalidated. Only provided (non-None) params are sent. `fields` defaults to `["pageviews", "visitors"]`. `events`, `pages` are lists joined with commas. Filters (`page`, `pages`, `country`, `referrer`, `utm_*`, `browser_name`, `os_name`, `device_type`) support wildcard values and are passed through verbatim.

- [ ] **Step 1: Write the failing tests**

`tests/test_stats.py`:

```python
"""Tests for the get_stats tool."""

import httpx
import respx
from fastmcp import FastMCP

from simpleanalytics_mcp.tools.stats import register_stats_tools


def _get_tool(mcp: FastMCP, name: str):
    return mcp._tool_manager._tools[name].fn


def _stats():
    mcp = FastMCP("test")
    register_stats_tools(mcp)
    return _get_tool(mcp, "get_stats")


@respx.mock
async def test_get_stats_defaults() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={"pageviews": 10, "visitors": 7})
    )
    get_stats = _stats()
    result = await get_stats(hostname="example.com")
    assert result == {"pageviews": 10, "visitors": 7}
    params = route.calls.last.request.url.params
    assert params["fields"] == "pageviews,visitors"
    assert params["version"] == "6"
    assert params["timezone"] == "America/Chicago"


@respx.mock
async def test_get_stats_passes_filters_and_lists() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={})
    )
    get_stats = _stats()
    await get_stats(
        hostname="example.com",
        fields=["pages", "referrers"],
        start="2026-06-01",
        end="2026-06-30",
        interval="day",
        limit=100,
        events=["signup", "purchase"],
        pages=["/blog/*", "/contact"],
        country="US",
        device_type="mobile",
    )
    params = route.calls.last.request.url.params
    assert params["fields"] == "pages,referrers"
    assert params["start"] == "2026-06-01"
    assert params["end"] == "2026-06-30"
    assert params["interval"] == "day"
    assert params["limit"] == "100"
    assert params["events"] == "signup,purchase"
    assert params["pages"] == "/blog/*,/contact"
    assert params["country"] == "US"
    assert params["device_type"] == "mobile"


@respx.mock
async def test_get_stats_omits_unset_params() -> None:
    route = respx.get("https://simpleanalytics.com/example.com.json").mock(
        return_value=httpx.Response(200, json={})
    )
    get_stats = _stats()
    await get_stats(hostname="example.com")
    params = route.calls.last.request.url.params
    assert "country" not in params
    assert "interval" not in params
    assert "events" not in params
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_stats.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'simpleanalytics_mcp.tools.stats'`.

- [ ] **Step 3: Write `src/simpleanalytics_mcp/tools/stats.py`**

```python
"""Aggregated statistics tool (Stats API) for SimpleAnalytics MCP."""

from typing import Any

from fastmcp import FastMCP

from simpleanalytics_mcp.client import default_timezone, get_json
from simpleanalytics_mcp.validation import parse_fields


def register_stats_tools(mcp: FastMCP) -> None:
    """Register the Stats API tool with the MCP server."""

    @mcp.tool()
    async def get_stats(
        hostname: str,
        fields: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        interval: str | None = None,
        limit: int | None = None,
        events: list[str] | None = None,
        timezone: str | None = None,
        page: str | None = None,
        pages: list[str] | None = None,
        country: str | None = None,
        referrer: str | None = None,
        utm_source: str | None = None,
        utm_medium: str | None = None,
        utm_campaign: str | None = None,
        utm_content: str | None = None,
        utm_term: str | None = None,
        browser_name: str | None = None,
        os_name: str | None = None,
        device_type: str | None = None,
    ) -> Any:
        """
        Get dashboard-accurate aggregated statistics from SimpleAnalytics.

        fields (default ["pageviews", "visitors"]) chooses what to return:
        pageviews, visitors, histogram, pages, countries, referrers,
        utm_sources, utm_mediums, utm_campaigns, utm_contents, utm_terms,
        browser_names, os_names, device_types, seconds_on_page.

        start/end accept YYYY-MM-DD or relative keywords (yesterday, today);
        they default on the API side to one month ago / today. interval controls
        histogram granularity (hour, day, week, month, year). limit is 1-1000.
        events counts specific event names (independent of filters).

        Filters narrow the data and support trailing-* wildcards: page, pages
        (e.g. ["/blog/*"]), country, referrer, utm_source, utm_medium,
        utm_campaign, utm_content, utm_term, browser_name, os_name, device_type.
        """
        params: dict[str, Any] = {
            "fields": parse_fields(fields if fields else ["pageviews", "visitors"]),
            "timezone": timezone or default_timezone(),
        }
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        if interval is not None:
            params["interval"] = interval
        if limit is not None:
            params["limit"] = limit
        if events:
            params["events"] = ",".join(events)
        if page is not None:
            params["page"] = page
        if pages:
            params["pages"] = ",".join(pages)
        if country is not None:
            params["country"] = country
        if referrer is not None:
            params["referrer"] = referrer
        if utm_source is not None:
            params["utm_source"] = utm_source
        if utm_medium is not None:
            params["utm_medium"] = utm_medium
        if utm_campaign is not None:
            params["utm_campaign"] = utm_campaign
        if utm_content is not None:
            params["utm_content"] = utm_content
        if utm_term is not None:
            params["utm_term"] = utm_term
        if browser_name is not None:
            params["browser_name"] = browser_name
        if os_name is not None:
            params["os_name"] = os_name
        if device_type is not None:
            params["device_type"] = device_type

        return await get_json(f"/{hostname}.json", params, need_user_id=False)
```

- [ ] **Step 4: Wire it into `server.py`**

Add the import near the top of `src/simpleanalytics_mcp/server.py`:

```python
from simpleanalytics_mcp.tools.stats import register_stats_tools
```

And call it inside `create_server()`, before `return mcp` (alongside the websites registration):

```python
    register_stats_tools(mcp)
```

- [ ] **Step 5: Add a registration test to `tests/test_server.py`**

Append to `tests/test_server.py`:

```python
def test_get_stats_registered() -> None:
    server = create_server()
    assert "get_stats" in server._tool_manager._tools
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_stats.py tests/test_server.py -v`
Expected: PASS.

- [ ] **Step 7: Run ruff and mypy**

Run: `ruff check . && mypy src`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add src/simpleanalytics_mcp/tools/stats.py src/simpleanalytics_mcp/server.py tests/test_stats.py tests/test_server.py
git commit -m "feat: add get_stats tool for Stats API aggregates"
```

---

### Task 6: `export_datapoints` tool (Export API + inline/file rule)

**Files:**
- Create: `src/simpleanalytics_mcp/tools/export.py`
- Modify: `src/simpleanalytics_mcp/server.py`
- Test: `tests/test_export.py`

**Interfaces:**
- Consumes: `get_json`, `default_timezone` from `client`; `parse_fields`, `validate_export_range` from `validation`.
- Produces: `register_export_tools(mcp: FastMCP) -> None`, registering async tool `export_datapoints(...) -> dict[str, Any]`. Also module helpers `_export_dir() -> Path`, `_inline_limit() -> int`, `write_export_file(rows, hostname, start, end, timestamp, export_dir) -> Path`.

Design decisions locked here (consistent with the spec's inline/file rule):
- The tool always requests `format=json` from the API so it can count rows and build a `sample_head`. It does not expose a user-facing `format` param in v1; large results are written to disk as newline-delimited JSON (`.ndjson`).
- `robots` defaults to `False` and is sent as the lowercase string `"false"`/`"true"`. `type` defaults to `"pageviews"`.
- Return shape:
  - inline (rows <= limit): `{"row_count": int, "fields": list[str], "inline": True, "rows": list}`
  - file (rows > limit): `{"row_count": int, "fields": list[str], "inline": False, "file_path": str, "sample_head": list}` (first 10 rows).
- The API returns a JSON array of row objects; if a dict is returned it is read from its `"data"` key, else treated as empty.

- [ ] **Step 1: Write the failing tests**

`tests/test_export.py`:

```python
"""Tests for the export_datapoints tool."""

import json
from pathlib import Path

import httpx
import pytest
import respx
from fastmcp import FastMCP

from simpleanalytics_mcp.tools.export import register_export_tools, write_export_file


def _get_tool(mcp: FastMCP, name: str):
    return mcp._tool_manager._tools[name].fn


def _export():
    mcp = FastMCP("test")
    register_export_tools(mcp)
    return _get_tool(mcp, "export_datapoints")


def _rows(n: int) -> list[dict[str, str]]:
    return [{"path": f"/p{i}", "added_iso": "2026-06-24T00:00:00Z"} for i in range(n)]


@respx.mock
async def test_export_inline_when_small() -> None:
    route = respx.get("https://simpleanalytics.com/api/export/datapoints").mock(
        return_value=httpx.Response(200, json=_rows(3))
    )
    export_datapoints = _export()
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
    export_datapoints = _export()
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
    export_datapoints = _export()
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_export.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'simpleanalytics_mcp.tools.export'`.

- [ ] **Step 3: Write `src/simpleanalytics_mcp/tools/export.py`**

```python
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
```

- [ ] **Step 4: Wire it into `server.py`**

Add the import near the top of `src/simpleanalytics_mcp/server.py`:

```python
from simpleanalytics_mcp.tools.export import register_export_tools
```

And call it inside `create_server()`, before `return mcp`:

```python
    register_export_tools(mcp)
```

- [ ] **Step 5: Add a registration test to `tests/test_server.py`**

Append to `tests/test_server.py`:

```python
def test_export_datapoints_registered() -> None:
    server = create_server()
    assert "export_datapoints" in server._tool_manager._tools
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_export.py tests/test_server.py -v`
Expected: PASS.

- [ ] **Step 7: Run the full suite, ruff, and mypy**

Run: `pytest -v && ruff check . && mypy src`
Expected: all tests PASS, no lint or type errors.

- [ ] **Step 8: Commit**

```bash
git add src/simpleanalytics_mcp/tools/export.py src/simpleanalytics_mcp/server.py tests/test_export.py tests/test_server.py
git commit -m "feat: add export_datapoints tool with inline/file output rule"
```

---

### Task 7: Packaging docs and configuration reference

**Files:**
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Create: `LICENSE`
- Create: `.env.example`

**Interfaces:**
- Consumes: the finished tool surface (three tools) and env-var contract.
- Produces: user-facing docs; no code.

- [ ] **Step 1: Create `.env.example`**

```bash
# SimpleAnalytics credentials (from account settings)
SA_API_KEY=sa_api_key_your_key_here
SA_USER_ID=sa_user_id_your_user_id_here

# Optional
SA_DEFAULT_TIMEZONE=America/Chicago
# SA_EXPORT_DIR=/path/for/large/exports   # defaults to the system temp dir
# SA_INLINE_ROW_LIMIT=500
```

- [ ] **Step 2: Create `LICENSE`**

Standard MIT License, copyright holder "84EM", year 2026.

- [ ] **Step 3: Create `README.md`**

````markdown
# SimpleAnalytics MCP

An MCP server for [SimpleAnalytics](https://simpleanalytics.com). Gives agents
access to SimpleAnalytics data so they can do SEO work and track real results,
including joining traffic data with Google Search Console and other sources.

## Tools

- **`get_stats`** — dashboard-accurate aggregates from the Stats API: pageviews,
  visitors, histogram, top pages, countries, referrers, all UTM breakdowns,
  browser/OS/device splits, seconds on page, and event counts. Supports filters
  (page, country, UTM, device, etc.) with trailing-`*` wildcards.
- **`export_datapoints`** — raw datapoints (one row per page view or event) from
  the Export API. Small results return inline; large results are written to a
  newline-delimited JSON file and summarized.
- **`list_websites`** — lists the hostnames in your account.

## Setup

```bash
pip install -e .
cp .env.example .env   # then fill in SA_API_KEY and SA_USER_ID
```

Get `SA_API_KEY` and `SA_USER_ID` from your SimpleAnalytics account settings.

## MCP client configuration

```json
{
  "mcpServers": {
    "simpleanalytics": {
      "command": "simpleanalytics-mcp",
      "env": {
        "SA_API_KEY": "sa_api_key_your_key_here",
        "SA_USER_ID": "sa_user_id_your_user_id_here"
      }
    }
  }
}
```

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SA_API_KEY` | yes | — | API key (`sa_api_key_...`) |
| `SA_USER_ID` | yes | — | User ID (`sa_user_id_...`), used by Export and list_websites |
| `SA_DEFAULT_TIMEZONE` | no | `America/Chicago` | Default timezone for queries |
| `SA_EXPORT_DIR` | no | system temp dir | Where large raw exports are written |
| `SA_INLINE_ROW_LIMIT` | no | `500` | Max rows returned inline before file output |

## Development

```bash
pip install -e ".[dev]"
pytest -v
ruff check .
mypy src
```
````

- [ ] **Step 4: Create `CHANGELOG.md`**

```markdown
# Changelog

All notable changes to this project are documented here. This project adheres to
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-06

### Added

- Initial release.
- `get_stats` tool wrapping the SimpleAnalytics Stats API.
- `export_datapoints` tool wrapping the Export API, with an inline/file output rule.
- `list_websites` tool for hostname discovery.
```

- [ ] **Step 5: Create `AGENTS.md`**

```markdown
# SimpleAnalytics MCP — Agent Notes

MCP server exposing the SimpleAnalytics Stats API, Export API, and website
discovery. Python 3.12, FastMCP, httpx.

## Layout

- `src/simpleanalytics_mcp/client.py` — async httpx client: auth headers, pinned
  API version (`6`), error mapping. All requests go through `get_json`.
- `src/simpleanalytics_mcp/validation.py` — pure input validation.
- `src/simpleanalytics_mcp/tools/` — one module per tool (`stats`, `export`,
  `websites`), each with a `register_*_tools(mcp)` function.
- `src/simpleanalytics_mcp/server.py` — builds the FastMCP server and registers tools.

## Conventions

- Credentials come only from the environment / `.env`. Never read arbitrary files.
- `fields` is an arbitrary passthrough — no field whitelist.
- All HTTP in tests is mocked with respx; no live calls in CI.

## Commands

- Test: `pytest -v`
- Lint: `ruff check .`
- Types: `mypy src`
```

- [ ] **Step 6: Create `CLAUDE.md`**

```markdown
See [AGENTS.md](AGENTS.md).
```

- [ ] **Step 7: Verify docs reference reality**

Run: `pytest -v`
Expected: full suite PASS (confirms the tool names and env vars named in the docs match the code).

- [ ] **Step 8: Commit**

```bash
git add README.md CHANGELOG.md AGENTS.md CLAUDE.md LICENSE .env.example
git commit -m "docs: add README, changelog, agent notes, and env example"
```

---

## Self-Review

**1. Spec coverage:**

- Stats API wrapper → Task 5 (`get_stats`), all documented fields + filters + wildcards.
- Export API wrapper → Task 6 (`export_datapoints`), arbitrary field passthrough, hourly validation, inline/file rule.
- Website discovery → Task 4 (`list_websites`).
- Architecture (client/validation/tools/server split, uptimerobot-mcp mirror) → Tasks 1-6.
- Config env vars (`SA_API_KEY`, `SA_USER_ID`, `SA_DEFAULT_TIMEZONE`, `SA_EXPORT_DIR`, `SA_INLINE_ROW_LIMIT`) → Task 3 (`default_timezone`, creds), Task 6 (`_export_dir`, `_inline_limit`), Task 7 (`.env.example`, README table).
- Version pin `6` → Task 3 (`API_VERSION`, injected in `get_json`).
- Auth (Api-Key always, User-Id for Export + list_websites) → Task 3 + tool `need_user_id` flags.
- Error handling (401/403 hint, generic status, transport) → Task 3, tested.
- Testing (mocked httpx, validation/client/export/stats coverage) → Tasks 2-6.
- Non-goals honored: no re-aggregation, three tools only, no caching/pagination, read-only.
- Deferred open items (websites JSON shape, datapoint/session_id resolution) → export tolerates list/dict shapes; passthrough handles undocumented fields; both confirmable via an optional live check post-build.

**2. Placeholder scan:** No TBD/TODO/"add error handling"/"similar to Task N" left; every code step has complete code. (LICENSE is described as standard MIT with a named holder/year — a well-known fixed text, not a code placeholder.)

**3. Type consistency:** `get_json(path, params, *, need_user_id)` signature identical across Tasks 3-6. `parse_fields(list[str]) -> str`, `validate_export_range(str, str)`, `default_timezone() -> str`, `write_export_file(rows, hostname, start, end, timestamp, export_dir) -> Path` used consistently with their definitions. Tool return shapes match their tests.

## Notes on optional live smoke test

The spec calls for an optional live smoke test gated behind an env var, skipped in CI. It is intentionally not a task above because it requires real credentials and network access. If desired after the build, add `tests/test_live_smoke.py` guarded by `pytest.skip` unless a `SA_LIVE_TESTS=1` env var (plus real `SA_API_KEY`/`SA_USER_ID`) is present, calling `list_websites` and a small `get_stats` against a real hostname to confirm the `/api/websites` JSON shape and that credentials work.
