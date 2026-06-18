from scripts.build_downstream_ready import first_blocking_reason


def test_ready_blocking_reason_uses_first_failure():
    reason = first_blocking_reason({"quality_check": "PASS", "acceptance_check": "FAIL", "smoke_check": "FAIL"})
    assert reason == "acceptance_check failed"


def test_ready_has_no_blocking_reason_for_warn():
    assert first_blocking_reason({"quality_check": "WARN", "acceptance_check": "PASS", "smoke_check": "PASS"}) is None
