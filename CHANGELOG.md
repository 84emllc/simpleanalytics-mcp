# Changelog

All notable changes to this project are documented here. This project adheres to
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-11

### Added

- `get_stats` accepts `metadata` filters (`metadata.<key>` on the Stats API).
- `get_stats` accepts `compare` to fetch the equal-length previous period and return the percent change for pageviews, visitors, seconds on page, and each event.
- `get_event_histogram` tool: one event counted per hour, day, week, month, or year, with filters, built from an events export.
- `get_recent_hits` tool: the last 60 minutes of page views and events, from hourly exports.

### Changed

- `export_datapoints` fetches through a shared `fetch_datapoints` helper.

### Fixed

- The `get_stats` description said event counts ignore filters. They respect filters. It also now notes that `end` is inclusive and that `events=["*"]` returns every event.

## [1.0.0] - 2026-07-07

### Added

- `get_stats` tool wrapping the SimpleAnalytics Stats API.
- `export_datapoints` tool wrapping the Export API, with an inline/file output rule.
- `list_websites` tool for hostname discovery.

### Fixed

- `export_datapoints` reads the datapoints key from the Export API response correctly.

## [0.1.0] - 2026-07-06

### Added

- Initial release.
- `get_stats` tool wrapping the SimpleAnalytics Stats API.
- `export_datapoints` tool wrapping the Export API, with an inline/file output rule.
- `list_websites` tool for hostname discovery.
