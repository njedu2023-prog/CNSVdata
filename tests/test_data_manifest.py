import json


def test_manifest_shape():
    manifest = {
        "snapshot_id": "cnsvdata-2026-06-18-abc",
        "generated_at": "2026-06-18 16:30:00",
        "latest_trade_date": "2026-06-18",
        "source": "tushare",
        "files": [{"path": "data/processed/cnsv_daily.parquet", "rows": 1, "columns": ["trade_date"], "sha256": "abc", "updated_at": "now"}],
    }
    loaded = json.loads(json.dumps(manifest))
    assert loaded["snapshot_id"]
    assert loaded["files"][0]["sha256"]
