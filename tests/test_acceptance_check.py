from cnsvdata.validators import aggregate_status
import scripts.acceptance_check as acceptance_check
from scripts.acceptance_check import required_file_checks


def test_acceptance_status_aggregation():
    assert aggregate_status([{"status": "PASS"}]) == "PASS"
    assert aggregate_status([{"status": "PASS"}, {"status": "WARN"}]) == "WARN"
    assert aggregate_status([{"status": "PASS"}, {"status": "FAIL"}]) == "FAIL"


def test_required_file_check_flags_missing():
    checks = required_file_checks(["definitely_missing.file"])
    assert checks[0]["status"] == "FAIL"


def test_missing_data_gaps_report_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(acceptance_check, "QUALITY_DIR", tmp_path)
    check = acceptance_check.data_gaps_status_check()
    assert check["status"] == "FAIL"
    assert check["detail"] == "missing_or_invalid_data_gaps"
