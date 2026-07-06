# SimpleAnalytics MCP — Design

Date: 2026-07-06
Status: Approved (design)

## Purpose

An MCP server that gives agents programmatic access to SimpleAnalytics data, so they can perform SEO work and track real results by joining SimpleAnalytics traffic data with other sources (Google Search Console, etc.). SimpleAnalytics is the analytics platform in use; Google Analytics is not.

The server wraps two SimpleAnalytics APIs:

- **Stats API** — SimpleAnalytics-computed aggregates (the numbers shown in the dashboard). Primary surface for SEO analysis and GSC joins.
- **Export API** — raw data points (one row per page view or event, no sampling). Row-level drilldown.

## Authoritative API facts

Verified by reading the live docs in a real browser (accordions expanded) rather than a fetched summary, because summaries hallucinate specifics and the field tables are inside collapsed `<details>` accordions.

### Stats API

- `GET https://simpleanalytics.com/{hostname}.json`
- Auth: `Api-Key: sa_api_key_...` header. Public websites can be read without credentials, but the server always sends the key.
- Query params: `version` (latest `6`), `start` (`YYYY-MM-DD`, defaults 1 month ago), `end` (defaults today), `limit` (1-1000), `timezone` (e.g. `Europe/Amsterdam`, capitals), `info` (default true), `events` (list of event names + counts), `interval` (`hour`|`day`|`week`|`month`|`year`; `hour` added in v6), `fields` (comma list).
- `fields` values: `pageviews`, `visitors`, `histogram`, `pages`, `countries`, `referrers`, `utm_sources`, `utm_mediums`, `utm_campaigns`, `utm_contents`, `utm_terms`, `browser_names`, `os_names`, `device_types`, `seconds_on_page`.
- Filters: `page`, `pages` (comma list, wildcards `/product/*`), `country`, `referrer`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `browser_name`, `os_name`, `device_type`. Wildcards supported via trailing `*`. Filters do not affect the `events` param.
- Per-page shorthand: path can be appended to the URL (`/{hostname}/contact.json`) instead of using `pages`.

### Export API

- `GET https://simpleanalytics.com/api/export/datapoints`
- Auth: BOTH `Api-Key: sa_api_key_...` and `User-Id: sa_user_id_...` headers required.
- Query params: `version` (`6`), `format` (`csv`|`json`|`ndjson`), `hostname`, `start`, `end`, `fields` (comma list), `robots` (`true`|`false`, optional), `timezone` (URL-encoded), `type` (e.g. `pageviews`).
- Date format: `YYYY-MM-DD`, or hourly `YYYY-MM-DDTHH` (HH 00-23). Hourly constraints: both `start` and `end` must include the hour, and `start` date must equal `end` date (single day only). Hours are in the specified timezone.
- Data streams directly from the database; docs state no practical size limit and mention no pagination or documented rate limit. Selecting fewer fields reduces payload.

### Export fields (documented)

Timing: `added_unix`, `added_iso`. Location/path: `hostname`, `hostname_original`, `path`, `query`. Analytics: `is_unique`, `is_robot`, `document_referrer`. UTM: `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`. Behavior: `scrolled_percentage`, `duration_seconds`. Device dims: `viewport_width`, `viewport_height`, `screen_width`, `screen_height`. Browser/system: `user_agent`, `device_type` (`desktop`|`mobile`|`tablet`|`tv`), `country_code`, `browser_name`, `browser_version`, `os_name`, `os_version`, `lang_region`, `lang_language`. Identity: `uuid` (page view id, not always unique). Custom: `metadata.***` (user-defined, type-suffixed: `_text`, `_date`, `_bool`, `_int`; `metadata.sa_urlparam_*` for allowed URL params).

Deprecated (kept for compatibility, avoid): `url`, `referrer`, `referrer_raw`, `device_width_pixels`, `device_width`, `source`.

**Discrepancy to respect:** the docs' CSV example includes columns `datapoint` (event name, e.g. `visit_homepage`, `popup_show`) and `session_id` that are NOT in the documented field table. Therefore the server must treat `fields` as an arbitrary passthrough list and must not enforce a documented-field whitelist. It validates only that tokens are non-empty; the API is the authority on which fields resolve.

### Discovery

- `GET https://simpleanalytics.com/api/websites` (needs `Api-Key` + `User-Id`) lists the account's websites/hostnames.

## Architecture

Match the newest single-API in-house MCP (`uptimerobot-mcp`, Feb 2026): Python 3.12, FastMCP, httpx, python-dotenv, `src/` layout, ruff + mypy (strict) + pytest.

```
simpleanalytics-mcp/
  pyproject.toml            # deps: fastmcp>=3, httpx>=0.28, python-dotenv>=1.1
  src/simpleanalytics_mcp/
    __init__.py
    __main__.py             # python -m simpleanalytics_mcp
    server.py               # FastMCP instance, tool registration, main()
    client.py               # httpx client: auth-header injection, base URLs, version pin, error mapping
    validation.py           # date + hourly-range, field-list parsing, format, timezone checks
    tools/
      __init__.py
      stats.py              # get_stats
      export.py             # export_datapoints (+ file-write helper)
      websites.py           # list_websites
  tests/
  .env.example
  README.md  CHANGELOG.md  AGENTS.md  CLAUDE.md  LICENSE
  .github/
```

Each unit has one job: `validation` is pure functions over inputs; `client` owns transport, auth, and error shape; each `tools/*` module owns one tool's parameter surface and result shaping; `server` only wires tools to the FastMCP instance.

## Configuration (environment)

Loaded via python-dotenv. Never read from arbitrary files; credentials live only in the environment / `.env`.

- `SA_API_KEY` (required) — `sa_api_key_...`
- `SA_USER_ID` (required for Export and list_websites) — `sa_user_id_...`
- `SA_DEFAULT_TIMEZONE` (optional, default `America/Chicago`)
- `SA_EXPORT_DIR` (optional, default the session scratchpad; where large raw exports are written)
- `SA_INLINE_ROW_LIMIT` (optional, default `500`)
- API `version` pinned to `6` as a constant, overridable per call.

## Tools

### 1. `get_stats` (Stats API)

Aggregated stats straight from SimpleAnalytics, so numbers match the dashboard. The workhorse for SEO analysis and GSC joins.

- Inputs: `hostname` (required), `fields` (list; default `["pageviews","visitors"]`), `start`, `end`, `interval`, `limit`, `events` (list), `timezone` (default from env), and filters (`page`, `pages`, `country`, `referrer`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `browser_name`, `os_name`, `device_type`). Wildcards allowed in filter values.
- Output: SimpleAnalytics JSON response, returned as-is (already compact aggregates).
- Notes: `events` counts are independent of filters (documented). Defaults for `start`/`end` follow the API (1 month ago / today) when omitted.

### 2. `export_datapoints` (Export API)

Raw, row-level data for drilldown.

- Inputs: `hostname` (required), `start`, `end` (required), `fields` (list, arbitrary passthrough; default a small useful set, e.g. `["added_iso","path","country_code","device_type"]`), `format` (default `ndjson` for file writes, `json` when returned inline), `robots` (default `false`), `type` (default `pageviews`), `timezone` (default from env).
- Validation: date format; hourly rule (if any bound has `THH`, both must, and `start` date must equal `end` date); non-empty field tokens; no field whitelist.
- Output rule (auto):
  - Fetch as JSON, count rows.
  - If rows <= `SA_INLINE_ROW_LIMIT`: return rows inline as JSON.
  - If rows > limit: write full dataset to `SA_EXPORT_DIR/{hostname}-{start}_{end}-{timestamp}.ndjson`, return `{row_count, fields, file_path, sample_head}` (first ~10 rows). Timestamp is supplied by the caller layer, not generated inside a workflow context.
- Rationale: raw exports can be tens of thousands of rows per month; inlining would blow up agent context, and agents aggregate large raw sets poorly. Small pulls stay ergonomic; large pulls stay safe and greppable on disk.

### 3. `list_websites` (Discovery)

Lists the account's hostnames so an agent can discover what it can query.

- Inputs: none (uses env credentials).
- Output: list of websites/hostnames from `GET /api/websites`.

## Data flow

`tool → validation → client → httpx GET → parse → shape`

- `client` injects `Api-Key` (always) and `User-Id` (Export, list_websites), builds the query string, pins `version=6`, sets a sane timeout.
- Stats results pass through as JSON.
- Export results are parsed to rows, then the inline/file rule is applied.

## Error handling

- Non-2xx responses map to a structured error: `{error, status, detail}` where `detail` is a trimmed body snippet.
- 401 / 403: message hints to check `SA_API_KEY` / `SA_USER_ID`.
- 400: surface the API's parameter error verbatim (trimmed).
- Timeouts and connection errors: explicit error, no silent retry loop, no fallback to a different transport.
- Empty result sets: return an explicit empty result (row_count 0 / empty aggregates), not an error.

## Testing

- pytest with a mocked httpx transport (respx or a custom mock transport). No live network calls in CI.
- Coverage:
  - `validation`: valid/invalid dates, hourly constraint enforcement, field-list parsing (including `metadata.*` and undocumented tokens passing through), format and timezone validation.
  - `client`: header injection per endpoint, query-string construction, `version` pin, error mapping for 400/401/403/timeout.
  - `export`: inline-vs-file threshold behavior, file contents match fetched rows, sample_head shape.
  - `stats`: params and filters serialized correctly; wildcard filter values preserved.
- Optional live smoke test gated behind an env var (real credentials), skipped by default and in CI.

## Non-goals (YAGNI)

- No server-side re-aggregation of raw exports (the Stats API already provides dashboard-accurate aggregates).
- No convenience wrappers beyond the three tools (e.g. separate `get_top_pages`) in v1 — `get_stats` covers them via `fields`.
- No caching layer, no pagination handling (API streams; none documented).
- No write operations (the SimpleAnalytics APIs here are read-only).

## Open items deferred to implementation

- Confirm the exact JSON shape of `GET /api/websites` (field names) during the first live smoke test; adjust `list_websites` output shaping accordingly.
- Confirm whether `datapoint` and `session_id` resolve as Export `fields` against a live account (they appear in the docs' CSV example); passthrough design already accommodates either outcome.
