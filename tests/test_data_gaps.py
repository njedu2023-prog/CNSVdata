import pandas as pd

from scripts.detect_data_gaps import (
    bounded_expected_dates,
    dates_in,
    expected_from_coverage_start,
    lag_tolerant_missing_date_check,
    minute_minutes_check,
    missing_date_check,
    open_trade_dates,
    recent_expected_dates,
    suggested_backfill_commands,
)


def test_open_trade_dates_filters_closed_days():
    calendar = pd.DataFrame({"cal_date": ["2026-06-17", "2026-06-18"], "is_open": [0, 1]})
    assert open_trade_dates(calendar) == ["2026-06-18"]


def test_bounded_expected_dates_excludes_future_calendar_dates():
    calendar = pd.DataFrame({"cal_date": ["2026-06-18", "2026-12-31"], "is_open": [1, 1]})
    assert bounded_expected_dates(calendar, "2026-06-18") == ["2026-06-18"]


def test_latest_daily_gap_fails():
    check = missing_date_check("daily_missing_trade_dates", ["2026-06-18"], set(), "2026-06-18", latest_fail=True)
    assert check["status"] == "FAIL"


def test_lag_tolerant_moneyflow_allows_one_recent_gap():
    check = lag_tolerant_missing_date_check("moneyflow_missing_trade_dates", ["2026-06-17", "2026-06-18"], {"2026-06-17"})
    assert check["status"] == "WARN"


def test_lag_tolerant_moneyflow_fails_consecutive_recent_gaps():
    check = lag_tolerant_missing_date_check("moneyflow_missing_trade_dates", ["2026-06-17", "2026-06-18"], set())
    assert check["status"] == "FAIL"


def test_dates_in_handles_missing_dataframe():
    assert dates_in(None) == set()


def test_recent_expected_dates_limits_historical_noise():
    expected = [f"2026-06-{day:02d}" for day in range(1, 31)]
    assert recent_expected_dates(expected, window=3) == ["2026-06-28", "2026-06-29", "2026-06-30"]


def test_minute_expected_dates_start_at_available_coverage():
    expected = ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]
    actual = {"2026-06-03", "2026-06-04"}
    assert expected_from_coverage_start(expected, actual, "2026-06-04") == ["2026-06-03", "2026-06-04"]


def test_minute_missing_minutes_uses_coverage_threshold():
    coverage = {"coverage_ratio": 0.9917, "missing_minutes": ["2026-06-18 11:30:00"]}
    assert minute_minutes_check(coverage)["status"] == "PASS"


def test_passed_minute_tolerated_missing_bar_does_not_suggest_backfill():
    commands = suggested_backfill_commands(
        {"status": "PASS", "missing_trade_dates": []},
        {"status": "PASS", "missing_trade_dates": [], "missing_minutes": ["2026-06-18 13:00:00"]},
        {"status": "PASS", "missing_trade_dates": []},
    )
    assert commands == []
