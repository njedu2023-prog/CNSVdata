from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

import cnsvdata.intraday as intraday


def test_realtime_ready_reports_true_market_cutoff(tmp_path, monkeypatch):
    raw = tmp_path / "cnsv_1min_intraday_1400.parquet"
    pd.DataFrame(
        [
            {
                "trade_time": "2026-07-16 14:10:00",
                "ts_code": "600150.SH",
                "open": 33.0,
                "high": 33.2,
                "low": 32.9,
                "close": 33.1,
                "vol": 100,
                "amount": 3310,
            }
        ]
    ).to_parquet(raw, index=False)
    monkeypatch.setattr(intraday, "INTRADAY_RAW_PATH", raw)
    monkeypatch.setattr(intraday, "INTRADAY_METADATA_DIR", tmp_path / "metadata")

    payload = intraday.build_intraday_realtime_ready(
        datetime(2026, 7, 16, 14, 18, tzinfo=ZoneInfo("Asia/Shanghai"))
    )

    assert payload["ready"] is True
    assert payload["status"] == "PASS"
    assert payload["trade_date"] == "20260716"
    assert payload["asof_time"] == "14:10:00"
    assert payload["asof_price"] == 33.1
    assert payload["lag_minutes"] == 8.0


def test_realtime_ready_rejects_previous_trade_day(tmp_path, monkeypatch):
    raw = tmp_path / "cnsv_1min_intraday_1400.parquet"
    pd.DataFrame(
        [
            {
                "trade_time": "2026-07-15 15:00:00",
                "ts_code": "600150.SH",
                "open": 33.0,
                "high": 33.2,
                "low": 32.9,
                "close": 33.1,
                "vol": 100,
                "amount": 3310,
            }
        ]
    ).to_parquet(raw, index=False)
    monkeypatch.setattr(intraday, "INTRADAY_RAW_PATH", raw)
    monkeypatch.setattr(intraday, "INTRADAY_METADATA_DIR", tmp_path / "metadata")

    payload = intraday.build_intraday_realtime_ready(
        datetime(2026, 7, 16, 9, 55, tzinfo=ZoneInfo("Asia/Shanghai"))
    )

    assert payload["ready"] is False
    assert payload["status"] == "FAIL"
