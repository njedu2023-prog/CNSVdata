from cnsvdata.intraday import ready_payload


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
