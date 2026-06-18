from cnsvdata.validators import aggregate_status
from scripts.smoke_downstream_read import read_required_parquet


def test_downstream_status_rules():
    assert aggregate_status([{"status": "PASS"}, {"status": "FAIL"}]) == "FAIL"
    assert aggregate_status([{"status": "PASS"}, {"status": "WARN"}]) == "WARN"


def test_missing_required_parquet_fails(tmp_path):
    _, checks = read_required_parquet(tmp_path / "missing.parquet", ["trade_date"], "missing")
    assert checks[0]["status"] == "FAIL"
