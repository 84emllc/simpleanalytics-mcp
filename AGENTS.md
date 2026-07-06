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
