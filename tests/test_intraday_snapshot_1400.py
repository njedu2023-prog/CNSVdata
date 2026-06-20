import pandas as pd

from cnsvdata.intraday import ASOF_TIME_SHORT, aggregate_intraday_bars, normalize_intraday_minutes, snapshot_summary


def sample_minutes():
    times = list(pd.date_range("2026-06-18 09:30:00", "2026-06-18 11:30:00", freq="min"))
    times += list(pd.date_range("2026-06-18 13:00:00", "2026-06-18 14:00:00", freq="min"))
    rows = []
    for idx, trade_time in enumerate(times):
        price = 10 + idx * 0.01
        rows.append(
            {
                "trade_time": trade_time.strftime("%Y-%m-%d %H:%M:%S"),
                "ts_code": "600150.SH",
                "open": price,
                "high": price + 0.05,
                "low": price - 0.05,
                "close": price + 0.01,
                "vol": 100 + idx,
                "amount": (100 + idx) * price,
            }
        )
    return pd.DataFrame(rows)


def test_snapshot_uses_only_asof_window_and_price_1400():
    df = sample_minutes()
    df.loc[len(df)] = {
        "trade_time": "2026-06-18 14:01:00",
        "ts_code": "600150.SH",
        "open": 99,
        "high": 99,
        "low": 99,
        "close": 99,
        "vol": 1,
        "amount": 99,
    }
    minute = normalize_intraday_minutes(df)
    assert minute["trade_time"].max() == "2026-06-18 14:00:00"
    snapshot = snapshot_summary(minute)
    assert snapshot["asof_time"] == ASOF_TIME_SHORT
    assert snapshot["asof_price_1400"] != 99
    assert snapshot["last_valid_trade_time"].endswith("14:00:00")


def test_intraday_aggregation_does_not_cross_lunch_break():
    minute = normalize_intraday_minutes(sample_minutes())
    out = aggregate_intraday_bars(minute, 15)
    assert set(out["session"]) == {"morning", "afternoon"}
    assert not ((out["bar_start_time"].str.endswith("11:30:00")) & (out["bar_end_time"].str.endswith("13:00:00"))).any()
