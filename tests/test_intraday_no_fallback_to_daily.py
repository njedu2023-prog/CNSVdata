import pandas as pd

import cnsvdata.intraday as intraday


def test_intraday_raw_missing_does_not_fallback_to_processed(tmp_path, monkeypatch):
    raw = tmp_path / "data" / "intraday" / "raw" / "cnsv_1min_intraday_1400.parquet"
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "trade_time": "2026-06-18 14:00:00",
                "ts_code": "600150.SH",
                "open": 10,
                "high": 10,
                "low": 10,
                "close": 10,
                "vol": 1,
                "amount": 10,
            }
        ]
    ).to_parquet(processed / "cnsv_1min.parquet", index=False)
    monkeypatch.setattr(intraday, "INTRADAY_RAW_PATH", raw)

    result = intraday.read_source_minutes()

    assert result.empty


def test_missing_intraday_raw_writes_fail_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(intraday, "INTRADAY_METADATA_DIR", tmp_path / "metadata" / "intraday")
    monkeypatch.setattr(intraday, "INTRADAY_QUALITY_DIR", tmp_path / "data" / "quality" / "intraday")

    ready = intraday.build_missing_source_ready()

    assert ready["status"] == "FAIL"
    assert ready["ready"] is False
    assert "missing_intraday_minute_source" in ready["reason"]
    assert ready["allowed_usage"]["can_run_daily_model"] is False
    assert ready["allowed_usage"]["can_run_intraday_model"] is False
