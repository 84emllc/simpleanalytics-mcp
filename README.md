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
```

Create a `.env` file in the project root and set `SA_API_KEY` and `SA_USER_ID`.
Get both values from your SimpleAnalytics account settings. See the environment
variables table below for the full list of supported settings.

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
