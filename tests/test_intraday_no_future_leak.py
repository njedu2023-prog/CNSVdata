from cnsvdata.intraday import normalize_intraday_minutes
from tests.test_intraday_snapshot_1400 import sample_minutes


def test_replay_source_discards_minutes_after_1400():
    df = sample_minutes()
    df.loc[len(df)] = {
        "trade_time": "2026-06-18 15:00:00",
        "ts_code": "600150.SH",
        "open": 20,
        "high": 20,
        "low": 20,
        "close": 20,
        "vol": 1,
        "amount": 20,
    }
    minute = normalize_intraday_minutes(df)
    assert minute["trade_time"].max().endswith("14:00:00")
    assert "15:00:00" not in minute["trade_time"].to_string()
