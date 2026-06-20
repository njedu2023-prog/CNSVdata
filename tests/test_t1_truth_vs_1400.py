import json

import pandas as pd
import pytest

import cnsvdata.intraday as intraday


def test_t1_truth_calculates_next_close_vs_1400(tmp_path, monkeypatch):
    snapshot_root = tmp_path / "snapshots"
    replay_root = tmp_path / "replay"
    label_root = tmp_path / "labels"
    processed = tmp_path / "processed"
    monkeypatch.setattr(intraday, "SNAPSHOT_ROOT", snapshot_root)
    monkeypatch.setattr(intraday, "REPLAY_ROOT", replay_root)
    monkeypatch.setattr(intraday, "LABEL_ROOT", label_root)
    monkeypatch.setattr(intraday, "PROCESSED_DIR", processed)
    path = replay_root / "20260618" / "1400"
    path.mkdir(parents=True)
    (path / "intraday_snapshot_1400.json").write_text(
        json.dumps({"trade_date": "20260618", "asof_time": "14:00", "ts_code": "600150.SH", "asof_price_1400": 10.0}),
        encoding="utf-8",
    )
    processed.mkdir()
    pd.DataFrame([{"trade_date": "20260618", "close": 10.5}, {"trade_date": "20260619", "close": 11.0}]).to_parquet(processed / "cnsv_daily.parquet", index=False)
    truth = intraday.build_t1_truth()
    row = truth.iloc[0]
    assert row["next_trade_date"] == "20260619"
    assert row["actual_return_vs_1400"] == pytest.approx(0.1)
    assert row["actual_up_label"] == 1
    assert bool(row["truth_ready"]) is True
