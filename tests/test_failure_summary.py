from scripts.build_failure_summary import render_markdown, suggested_action


def test_failure_summary_markdown_contains_actions():
    payload = {
        "status": "FAIL",
        "blocking": True,
        "blocking_reason": "core minute parquet missing",
        "can_cnsv_main_start": False,
        "failed_count": 1,
        "warn_count": 0,
        "top_failures": [{"source": "acceptance", "name": "minute_missing", "status": "FAIL", "detail": "missing", "suggested_action": "rerun fetch_minute"}],
        "top_warnings": [],
        "concrete_missing_dates": {"minute": ["20260618"]},
        "suggested_backfill_commands": ["python scripts/backfill_missing_data.py --minute"],
        "allowed_usage": {"can_develop_cnsv_main_program": False},
        "next_action": "rerun fetch_minute",
    }
    text = render_markdown(payload)
    assert "Overall Status" in text
    assert "Can CNSV Main Start?" in text
    assert "Concrete Missing Dates" in text
    assert "Allowed Usage" in text
    assert "rerun fetch_minute" in text


def test_suggested_action_routes_by_dataset():
    assert "fetch_minute" in suggested_action("minute_missing")
    assert "fetch_moneyflow" in suggested_action("moneyflow_missing")
