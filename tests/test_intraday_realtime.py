from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

import cnsvdata.intraday as intraday


def _calendar(path):
    pd.DataFrame(
        {
            "cal_date": ["20260715", "20260716", "20260717"],
            "is_open": [1, 1, 1],
        }
    ).to_parquet(path, index=False)


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
    calendar = tmp_path / "trade_calendar.parquet"
    _calendar(calendar)
    monkeypatch.setattr(intraday, "TRADE_CALENDAR_CANDIDATES", (calendar,))

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
    calendar = tmp_path / "trade_calendar.parquet"
    _calendar(calendar)
    monkeypatch.setattr(intraday, "TRADE_CALENDAR_CANDIDATES", (calendar,))

    payload = intraday.build_intraday_realtime_ready(
        datetime(2026, 7, 16, 9, 55, tzinfo=ZoneInfo("Asia/Shanghai"))
    )

    assert payload["ready"] is False
    assert payload["status"] == "FAIL"


def test_realtime_ready_uses_previous_open_day_before_market_open(tmp_path, monkeypatch):
    raw = tmp_path / "cnsv_1min_intraday_1400.parquet"
    pd.DataFrame(
        [
            {
                "trade_time": "2026-07-16 15:00:00",
                "ts_code": "600150.SH",
                "open": 34.0,
                "high": 34.1,
                "low": 32.9,
                "close": 33.0,
                "vol": 100,
                "amount": 3300,
            }
        ]
    ).to_parquet(raw, index=False)
    calendar = tmp_path / "trade_calendar.parquet"
    _calendar(calendar)
    monkeypatch.setattr(intraday, "INTRADAY_RAW_PATH", raw)
    monkeypatch.setattr(intraday, "INTRADAY_METADATA_DIR", tmp_path / "metadata")
    monkeypatch.setattr(intraday, "TRADE_CALENDAR_CANDIDATES", (calendar,))

    payload = intraday.build_intraday_realtime_ready(
        datetime(2026, 7, 17, 0, 4, tzinfo=ZoneInfo("Asia/Shanghai"))
    )

    assert payload["ready"] is True
    assert payload["status"] == "PASS"
    assert payload["trade_date"] == "20260716"
    assert payload["expected_trade_date"] == "20260716"
    assert payload["blocking_reason"] is None


def test_cnsvdata_only_archives_intraday_history_after_main_program_final_run():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/fetch_intraday_realtime.yml").read_text(encoding="utf-8")

    assert workflow.count("- cron:") == 1
    assert '- cron: "34 12 * * 1-5"' in workflow
    assert "CNSV itself fetches Tushare realtime data in-session" in workflow
    assert 'cron: "4 12 * * 1-5"' not in workflow
