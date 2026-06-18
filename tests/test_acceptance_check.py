from cnsvdata.validators import aggregate_status
from scripts.acceptance_check import required_file_checks


def test_acceptance_status_aggregation():
    assert aggregate_status([{"status": "PASS"}]) == "PASS"
    assert aggregate_status([{"status": "PASS"}, {"status": "WARN"}]) == "WARN"
    assert aggregate_status([{"status": "PASS"}, {"status": "FAIL"}]) == "FAIL"


def test_required_file_check_flags_missing():
    checks = required_file_checks(["definitely_missing.file"])
    assert checks[0]["status"] == "FAIL"
