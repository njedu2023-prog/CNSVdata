import pandas as pd

from cnsvdata.validators import (
    aggregate_status,
    duplicate_count,
    invalid_a_share_minute_times,
    missing_columns,
    minute_coverage,
    numeric_validity_errors,
    ohlc_errors,
)


def test_ohlc_errors_accepts_valid_bar():
    df = pd.DataFrame({"open": [10], "high": [11], "low": [9], "close": [10.5]})
    assert ohlc_errors(df) == 0


def test_ohlc_errors_rejects_high_below_low():
    df = pd.DataFrame({"open": [10], "high": [8], "low": [9], "close": [9.5]})
    assert ohlc_errors(df) == 1


def test_basic_quality_helpers():
    df = pd.DataFrame({"trade_time": ["2026-06-19 09:30:00", "2026-06-19 09:30:00"], "x": [1, 2]})
    assert duplicate_count(df, ["trade_time"]) == 1
    assert missing_columns(df, ["trade_time", "missing"]) == ["missing"]


def test_minute_coverage_shape():
    df = pd.DataFrame({"trade_time": ["2026-06-19 09:30:00"], "trade_date": ["2026-06-19"]})
    report = minute_coverage(df)
    assert {"expected_minutes", "actual_minutes", "coverage_ratio"} <= set(report)


def test_invalid_a_share_minute_times_detects_break():
    df = pd.DataFrame({"trade_time": ["2026-06-19 12:00:00", "2026-06-19 14:00:00"]})
    assert invalid_a_share_minute_times(df) == ["2026-06-19 12:00:00"]


def test_numeric_validity_and_status_aggregation():
    df = pd.DataFrame({"open": [0], "vol": [-1], "amount": [1]})
    errors = numeric_validity_errors(df, ["open", "vol", "amount"])
    assert errors["open"] == 1
    assert errors["vol"] == 1
    assert aggregate_status([{"status": "PASS"}, {"status": "WARN"}]) == "WARN"
    assert aggregate_status([{"status": "WARN"}, {"status": "FAIL"}]) == "FAIL"
