import pandas as pd

from scripts.detect_data_gaps import bounded_expected_dates, dates_in, missing_date_check, open_trade_dates


def test_open_trade_dates_filters_closed_days():
    calendar = pd.DataFrame({"cal_date": ["2026-06-17", "2026-06-18"], "is_open": [0, 1]})
    assert open_trade_dates(calendar) == ["2026-06-18"]


def test_bounded_expected_dates_excludes_future_calendar_dates():
    calendar = pd.DataFrame({"cal_date": ["2026-06-18", "2026-12-31"], "is_open": [1, 1]})
    assert bounded_expected_dates(calendar, "2026-06-18") == ["2026-06-18"]


def test_latest_daily_gap_fails():
    check = missing_date_check("daily_missing_trade_dates", ["2026-06-18"], set(), "2026-06-18", latest_fail=True)
    assert check["status"] == "FAIL"


def test_dates_in_handles_missing_dataframe():
    assert dates_in(None) == set()
