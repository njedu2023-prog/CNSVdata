from scripts.build_downstream_ready import allowed_usage, first_blocking_reason, report_failure_reason


def test_ready_blocking_reason_uses_first_failure():
    reason = first_blocking_reason({"quality_check": "PASS", "acceptance_check": "FAIL", "smoke_check": "FAIL"})
    assert reason == "acceptance_check failed"


def test_ready_has_no_blocking_reason_for_warn():
    assert first_blocking_reason({"quality_check": "WARN", "acceptance_check": "PASS", "smoke_check": "PASS"}) is None


def test_report_failure_reason_summarizes_missing_minute_core():
    report = {
        "checks": [
            {"name": "required_file:data/processed/cnsv_1min.parquet", "status": "FAIL", "detail": "missing"},
            {"name": "moneyflow_core_nulls", "status": "WARN"},
        ]
    }
    assert report_failure_reason(report) == "core minute parquet missing"


def test_allowed_usage_warn_allows_connection_but_not_backtest():
    usage = allowed_usage("WARN", [{"source": "quality", "name": "moneyflow_core_nulls"}])
    assert usage["can_develop_cnsv_main_program"] is True
    assert usage["can_run_daily_ingest"] is True
    assert usage["can_run_backtest"] is False
    assert usage["can_use_moneyflow_as_strong_factor"] is False
    assert usage["can_generate_formal_signal"] is False


def test_allowed_usage_fail_blocks_all_downstream_use():
    usage = allowed_usage("FAIL", [])
    assert not any(usage.values())
