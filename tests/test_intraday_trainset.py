import pandas as pd

from cnsvdata.intraday import FEATURE_VERSION, LABEL_VERSION, check_trainset_no_future_leak


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


def test_trainset_quality_accepts_neutral_feature_and_label_versions():
    trainset = pd.DataFrame(
        [
            {
                "trade_date": "20260618",
                "feature_return_from_open_to_1400": 0.01,
                "actual_up_label": 1,
                "feature_version": FEATURE_VERSION,
                "label_version": LABEL_VERSION,
            }
        ]
    )
    report = check_trainset_no_future_leak(trainset)
    assert report["status"] == "PASS"
