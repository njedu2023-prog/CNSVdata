import json

import pandas as pd

import scripts.backfill_intraday_1min_history as backfill


def _calendar(path):
    pd.DataFrame(
        {
            "cal_date": ["20260617", "20260618", "20260619"],
            "is_open": [1, 1, 0],
            "exchange": ["SSE", "SSE", "SSE"],
        }
    ).to_parquet(path, index=False)


def _minutes(trade_date):
    return pd.DataFrame(
        [
            {
                "trade_time": f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]} 13:59:00",
                "ts_code": "600150.SH",
                "open": 10.0,
                "high": 10.2,
                "low": 9.9,
                "close": 10.1,
                "vol": 100,
                "amount": 1010,
            },
            {
                "trade_time": f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]} 14:00:00",
                "ts_code": "600150.SH",
                "open": 10.1,
                "high": 10.3,
                "low": 10.0,
                "close": 10.2,
                "vol": 100,
                "amount": 1020,
            },
            {
                "trade_time": f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]} 14:01:00",
                "ts_code": "600150.SH",
                "open": 99.0,
                "high": 99.0,
                "low": 99.0,
                "close": 99.0,
                "vol": 1,
                "amount": 99,
            },
        ]
    )


class FakePro:
    def stk_mins(self, **kwargs):
        return _minutes(kwargs["start_date"])


def test_backfill_writes_1400_raw_and_filters_future_minutes(tmp_path, monkeypatch):
    cal_path = tmp_path / "trade_calendar.parquet"
    raw_path = tmp_path / "data" / "intraday" / "raw" / "cnsv_1min_intraday_1400.parquet"
    report_path = tmp_path / "data" / "quality" / "intraday" / "intraday_backfill_latest.json"
    _calendar(cal_path)
    monkeypatch.setattr(backfill, "calendar_path", lambda: cal_path)
    monkeypatch.setattr(backfill, "INTRADAY_RAW_PATH", raw_path)
    monkeypatch.setattr(backfill, "BACKFILL_REPORT_PATH", report_path)
    monkeypatch.setattr(backfill, "get_tushare_pro", lambda: FakePro())
    monkeypatch.setattr(backfill, "load_yaml", lambda name: {"target": {"ts_code": "600150.SH", "name": "中国船舶"}, "tushare": {"minute_freq": "1min", "retry_times": 1, "retry_sleep_seconds": 0}}[name.removesuffix(".yml")])

    report = backfill.backfill_intraday_1min_history(2, "20260618", "600150.SH")

    out = pd.read_parquet(raw_path)
    assert report["status"] == "PASS"
    assert report["actual_trade_days"] == 2
    assert report["can_train_model"] is True
    assert out["trade_time"].str.endswith("14:01:00").sum() == 0
    assert out["trade_time"].str.endswith("14:00:00").sum() == 2
    assert {"trade_date", "trade_time", "ts_code", "name", "open", "high", "low", "close", "volume", "amount", "source", "created_at", "session", "bar_index"} <= set(out.columns)


def test_backfill_permission_failure_writes_fail_report(tmp_path, monkeypatch):
    cal_path = tmp_path / "trade_calendar.parquet"
    raw_path = tmp_path / "data" / "intraday" / "raw" / "cnsv_1min_intraday_1400.parquet"
    report_path = tmp_path / "data" / "quality" / "intraday" / "intraday_backfill_latest.json"
    _calendar(cal_path)
    monkeypatch.setattr(backfill, "calendar_path", lambda: cal_path)
    monkeypatch.setattr(backfill, "INTRADAY_RAW_PATH", raw_path)
    monkeypatch.setattr(backfill, "BACKFILL_REPORT_PATH", report_path)
    monkeypatch.setattr(backfill, "get_tushare_pro", lambda: (_ for _ in ()).throw(RuntimeError("TUSHARE_TOKEN is not configured")))
    monkeypatch.setattr(backfill, "load_yaml", lambda name: {"target": {"ts_code": "600150.SH"}, "tushare": {"retry_times": 1, "retry_sleep_seconds": 0}}[name.removesuffix(".yml")])

    report = backfill.backfill_intraday_1min_history(2, "20260618", "600150.SH")
    saved = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["status"] == "FAIL"
    assert saved["reason"] == "source_permission_insufficient"
    assert saved["actual_trade_days"] == 0
    assert saved["required_trade_days"] == 2
    assert saved["can_train_model"] is False
