import pandas as pd

from cnsvdata.intraday import (
    FEATURE_COLUMNS,
    FEATURE_VERSION,
    LABEL_VERSION,
    MIN_INTRADAY_TRAIN_ROWS,
    check_trainset_no_future_leak,
)


def test_trainset_quality_blocks_prediction_columns():
    trainset = pd.DataFrame(
        [
            {
                "trade_date": "20260618",
                "feature_return_from_open_to_1400": 0.01,
                "pred_up_prob": 0.7,
                "feature_version": FEATURE_VERSION,
                "label_version": LABEL_VERSION,
            }
        ]
    )
    report = check_trainset_no_future_leak(trainset)
    assert report["status"] == "FAIL"


def test_trainset_quality_warns_when_valid_trainset_is_too_small():
    row = {name: 0.01 for name in FEATURE_COLUMNS}
    row.update({"trade_date": "20260618", "actual_up_label": 1, "feature_version": FEATURE_VERSION, "label_version": LABEL_VERSION})
    trainset = pd.DataFrame([row])
    report = check_trainset_no_future_leak(trainset)
    assert report["status"] == "WARN"
    assert report["can_train_model"] is False


def test_trainset_quality_accepts_minimum_valid_training_history():
    rows = []
    for index in range(MIN_INTRADAY_TRAIN_ROWS):
        row = {name: 0.01 for name in FEATURE_COLUMNS}
        row.update({
            "trade_date": f"2026{index + 1:04d}",
            "actual_up_label": index % 2,
            "feature_version": FEATURE_VERSION,
            "label_version": LABEL_VERSION,
        })
        rows.append(row)

    report = check_trainset_no_future_leak(pd.DataFrame(rows))

    assert report["status"] == "PASS"
    assert report["can_train_model"] is True
