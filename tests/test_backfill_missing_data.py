from argparse import Namespace

from scripts.backfill_missing_data import datasets_from_gap_payload, selected_datasets


def test_selected_datasets_from_flags():
    args = Namespace(daily=True, minute=False, moneyflow=True, from_gap_report=False)
    assert selected_datasets(args) == ["daily", "moneyflow"]


def test_structured_gap_payload_selects_datasets():
    payload = {
        "daily": {"missing_trade_dates": []},
        "minute": {"missing_trade_dates": ["20260618"], "missing_minutes": []},
        "moneyflow": {"missing_trade_dates": ["20260617"]},
    }
    assert datasets_from_gap_payload(payload) == ["minute", "moneyflow"]
