import pandas as pd

from cnsvdata.validators import (
    aggregate_status,
    derive_moneyflow_net_amount,
    duplicate_count,
    invalid_a_share_minute_times,
    missing_columns,
    minute_coverage,
    moneyflow_null_check,
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


def test_moneyflow_one_day_null_is_warning():
    df = pd.DataFrame({"trade_date": ["2026-06-17", "2026-06-18"], "net_mf_amount": [1.0, None]})
    check = moneyflow_null_check(df, "2026-06-18")
    assert check["status"] == "WARN"
    assert check["detail"] == "latest_moneyflow_may_lag_one_trading_day"


def test_moneyflow_consecutive_recent_nulls_fail():
    df = pd.DataFrame({"trade_date": ["2026-06-17", "2026-06-18"], "net_mf_amount": [None, None]})
    check = moneyflow_null_check(df, "2026-06-18")
    assert check["status"] == "FAIL"


def test_moneyflow_net_amount_can_be_derived_from_components():
    df = pd.DataFrame(
        {
            "trade_date": ["2010-02-09"],
            "buy_sm_amount": [10],
            "sell_sm_amount": [1],
            "buy_md_amount": [20],
            "sell_md_amount": [2],
            "buy_lg_amount": [30],
            "sell_lg_amount": [3],
            "buy_elg_amount": [40],
            "sell_elg_amount": [None],
            "net_mf_amount": [None],
        }
    )
    repaired, stats = derive_moneyflow_net_amount(df)
    assert stats["derived_count"] == 1
    assert repaired.loc[0, "net_mf_amount"] == 94
    check = moneyflow_null_check(df, "2010-02-09")
    assert check["status"] == "PASS"
    assert check["detail"] == "derived_from_components"
