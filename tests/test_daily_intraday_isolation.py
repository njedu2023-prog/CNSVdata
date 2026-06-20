import json

import pandas as pd

import cnsvdata.daily as daily
import cnsvdata.intraday as intraday


def test_daily_pass_does_not_make_intraday_pass(tmp_path, monkeypatch):
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    pd.DataFrame([{"trade_date": "20260618", "close": 10.0}]).to_parquet(processed / "cnsv_daily.parquet", index=False)
    pd.DataFrame([{"trade_date": "20260618", "net_mf_amount": 1.0}]).to_parquet(processed / "cnsv_moneyflow.parquet", index=False)
    pd.DataFrame([{"cal_date": "20260618", "is_open": 1}]).to_parquet(processed / "trade_calendar.parquet", index=False)

    monkeypatch.setattr(daily, "PROCESSED_DIR", processed)
    monkeypatch.setattr(daily, "LEGACY_DAILY_CORE_FILES", {name: processed / path.name for name, path in daily.LEGACY_DAILY_CORE_FILES.items()})
    monkeypatch.setattr(daily, "DAILY_METADATA_DIR", tmp_path / "metadata" / "daily")
    monkeypatch.setattr(daily, "DAILY_QUALITY_DIR", tmp_path / "data" / "quality" / "daily")
    monkeypatch.setattr(intraday, "INTRADAY_RAW_PATH", tmp_path / "data" / "intraday" / "raw" / "missing.parquet")
    monkeypatch.setattr(intraday, "INTRADAY_METADATA_DIR", tmp_path / "metadata" / "intraday")
    monkeypatch.setattr(intraday, "INTRADAY_QUALITY_DIR", tmp_path / "data" / "quality" / "intraday")

    daily_ready = daily.build_daily_ready()
    intraday_ready = intraday.build_missing_source_ready()

    assert daily_ready["status"] == "PASS"
    assert daily_ready["allowed_usage"]["can_run_intraday_model"] is False
    assert intraday_ready["status"] == "FAIL"
    assert intraday_ready["allowed_usage"]["can_run_daily_model"] is False
    assert json.loads((tmp_path / "metadata" / "daily" / "daily_ready.json").read_text())["line"] == "daily"
    assert json.loads((tmp_path / "metadata" / "intraday" / "intraday_ready_1400.json").read_text())["line"] == "intraday_1400"
