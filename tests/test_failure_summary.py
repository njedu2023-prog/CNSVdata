from scripts.build_failure_summary import render_markdown, suggested_action


def test_failure_summary_markdown_contains_actions():
    payload = {
        "status": "FAIL",
        "blocking": True,
        "top_failures": [{"source": "acceptance", "name": "minute_missing", "status": "FAIL", "detail": "missing", "suggested_action": "rerun fetch_minute"}],
        "top_warnings": [],
    }
    text = render_markdown(payload)
    assert "Overall Status" in text
    assert "rerun fetch_minute" in text


def test_suggested_action_routes_by_dataset():
    assert "fetch_minute" in suggested_action("minute_missing")
    assert "fetch_moneyflow" in suggested_action("moneyflow_missing")
