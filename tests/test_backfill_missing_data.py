from argparse import Namespace

from scripts.backfill_missing_data import selected_datasets


def test_selected_datasets_from_flags():
    args = Namespace(daily=True, minute=False, moneyflow=True, from_gap_report=False)
    assert selected_datasets(args) == ["daily", "moneyflow"]
