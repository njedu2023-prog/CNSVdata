import json

from cnsvdata import intraday
from cnsvdata.intraday import ready_payload
from tests.test_intraday_snapshot_1400 import sample_minutes


class DummyPaths:
    root = type("P", (), {"relative_to": lambda self, root: "data/intraday/snapshots/20260618/1400"})()
    quality = type("P", (), {"relative_to": lambda self, root: "data/intraday/snapshots/20260618/1400/intraday_quality_1400.json"})()
    manifest = type("P", (), {"relative_to": lambda self, root: "data/intraday/snapshots/20260618/1400/intraday_manifest_1400.json"})()


def test_intraday_ready_allows_forecast_but_never_formal_signal():
    quality = {"status": "WARN", "checks": []}
    manifest = {"trade_date": "20260618", "files": [{"path": "x", "exists": True}]}
    ready = ready_payload(DummyPaths(), quality, manifest)
    assert ready["ready"] is True
    assert ready["allowed_usage"]["can_run_intraday_forecast"] is True
    assert ready["allowed_usage"]["can_generate_formal_signal"] is False


def test_replay_bundle_writes_ready_before_final_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(intraday, "REPLAY_ROOT", tmp_path / "replay")
    monkeypatch.setattr(intraday, "SNAPSHOT_ROOT", tmp_path / "snapshots")
    monkeypatch.setattr(intraday, "INTRADAY_METADATA_DIR", tmp_path / "metadata" / "intraday")
    monkeypatch.setattr(intraday, "INTRADAY_QUALITY_DIR", tmp_path / "quality" / "intraday")

    bundle = intraday.write_snapshot_bundle(sample_minutes(), "20260618", "replay")
    replay_ready_path = tmp_path / "replay" / "20260618" / "1400" / "intraday_ready_1400.json"
    replay_manifest_path = tmp_path / "replay" / "20260618" / "1400" / "intraday_manifest_1400.json"

    assert replay_ready_path.exists()
    assert replay_manifest_path.exists()
    manifest = json.loads(replay_manifest_path.read_text(encoding="utf-8"))
    ready = json.loads(replay_ready_path.read_text(encoding="utf-8"))

    assert all(item["exists"] for item in manifest["files"])
    assert "manifest_missing_files" not in ready["reason"]
    assert ready["snapshot_type"] == "replay"
    assert ready["replay"] is True
    assert ready["allowed_usage"]["can_run_daily_model"] is False
    assert ready["allowed_usage"]["can_run_backtest"] is True
    assert ready["allowed_usage"]["can_train_model"] is True
    assert ready["allowed_usage"]["can_generate_formal_signal"] is False
    assert bundle["manifest"]["files"][-1]["path"].endswith("intraday_ready_1400.json")
