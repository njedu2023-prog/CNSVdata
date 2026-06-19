from scripts.build_failure_summary import build_backfill_plan, render_markdown, suggested_action


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
        "backfill_plan": {
            "sop": "docs/minute_backfill_sop.md",
            "decision": "backfill_required_before_formal_backtest",
            "reason": "minute active gaps exist",
            "coverage_scope": "available_window:2026-06-09..2026-06-18",
            "active_missing_count": 1,
            "historical_missing_count": 3987,
            "command_when_required": "python scripts/backfill_missing_data.py --minute",
        },
        "allowed_usage": {"can_develop_cnsv_main_program": False},
        "next_action": "rerun fetch_minute",
    }
    text = render_markdown(payload)
    assert "Overall Status" in text
    assert "Can CNSV Main Start?" in text
    assert "Concrete Missing Dates" in text
    assert "Allowed Usage" in text
    assert "Minute Backfill Plan" in text
    assert "rerun fetch_minute" in text


def test_suggested_action_routes_by_dataset():
    assert "fetch_minute" in suggested_action("minute_missing")
    assert "fetch_moneyflow" in suggested_action("moneyflow_missing")


def test_backfill_plan_documents_historical_minute_gaps_without_current_blocker():
    plan = build_backfill_plan(
        {
            "status": "PASS",
            "historical_reference": {"minute_missing_count": 3987},
            "minute": {
                "status": "PASS",
                "missing_trade_dates": [],
                "missing_minutes": ["2026-06-18 13:00:00"],
                "coverage_scope": "available_window:2026-06-09..2026-06-18",
            },
        }
    )
    assert plan["decision"] == "not_required_for_current_readiness"
    assert plan["active_missing_count"] == 0
    assert plan["historical_missing_count"] == 3987
    assert plan["sop"] == "docs/minute_backfill_sop.md"
