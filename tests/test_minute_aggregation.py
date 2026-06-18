import pandas as pd

from scripts.build_minute_bars import aggregate_minutes


def test_aggregate_5min_uses_ohlcv_rules():
    df = pd.DataFrame(
        [
            {"ts_code": "600150.SH", "trade_time": "2026-06-18 09:30:00", "trade_date": "2026-06-18", "time": "09:30:00", "open": 10, "high": 11, "low": 9, "close": 10.5, "vol": 1, "amount": 10, "fetched_at": "x"},
            {"ts_code": "600150.SH", "trade_time": "2026-06-18 09:31:00", "trade_date": "2026-06-18", "time": "09:31:00", "open": 10.5, "high": 12, "low": 10, "close": 11, "vol": 2, "amount": 20, "fetched_at": "x"},
            {"ts_code": "600150.SH", "trade_time": "2026-06-18 09:32:00", "trade_date": "2026-06-18", "time": "09:32:00", "open": 11, "high": 11.5, "low": 8, "close": 9, "vol": 3, "amount": 30, "fetched_at": "x"},
        ]
    )
    out = aggregate_minutes(df, "5min")
    row = out.iloc[0]
    assert row["open"] == 10
    assert row["high"] == 12
    assert row["low"] == 8
    assert row["close"] == 9
    assert row["vol"] == 6
    assert row["amount"] == 60
