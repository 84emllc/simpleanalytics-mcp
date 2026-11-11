"""Tests for input validation helpers."""

import pytest

from simpleanalytics_mcp.validation import (
    is_hourly,
    metadata_params,
    parse_fields,
    previous_period,
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


def test_metadata_params_prefixes_keys() -> None:
    assert metadata_params({"plan": "pro", "tier_2": "x"}) == {
        "metadata.plan": "pro",
        "metadata.tier_2": "x",
    }


def test_metadata_params_rejects_bad_key() -> None:
    with pytest.raises(ValueError, match="metadata key"):
        metadata_params({"plan.x": "pro"})


def test_metadata_params_rejects_too_many_keys() -> None:
    with pytest.raises(ValueError, match="at most 20"):
        metadata_params({f"k{i}": "v" for i in range(21)})


def test_previous_period_same_length_ending_day_before() -> None:
    assert previous_period("2026-10-13", "2026-11-11") == ("2026-09-13", "2026-10-12")


def test_previous_period_single_day() -> None:
    assert previous_period("2026-11-11", "2026-11-11") == ("2026-11-10", "2026-11-10")


def test_previous_period_rejects_placeholders() -> None:
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        previous_period("today-30d", "today")


def test_previous_period_rejects_reversed_range() -> None:
    with pytest.raises(ValueError, match="after"):
        previous_period("2026-11-11", "2026-11-01")
