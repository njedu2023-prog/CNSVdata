from cnsvdata.intraday import DEFAULT_HISTORY_DAYS, latest_150_trade_window


def test_intraday_history_default_requires_150_trade_days():
    assert DEFAULT_HISTORY_DAYS == 150


def test_latest_150_trade_window_selects_last_150_open_days(tmp_path):
    path = tmp_path / "trade_calendar.parquet"
    rows = [{"cal_date": f"2026{i:04d}", "is_open": 1} for i in range(1, 181)]
    import pandas as pd

    pd.DataFrame(rows).to_parquet(path, index=False)
    start, end, dates = latest_150_trade_window(path)
    assert len(dates) == 150
    assert start == "20260031"
    assert end == "20260180"
