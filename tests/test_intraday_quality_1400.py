import pandas as pd

from cnsvdata.intraday import normalize_intraday_minutes, quality_report
from tests.test_intraday_snapshot_1400 import sample_minutes


def test_quality_fails_when_last_valid_minute_before_1355():
    df = sample_minutes()
    df = df[pd.to_datetime(df["trade_time"]).dt.strftime("%H:%M:%S") < "13:55:00"]
    report = quality_report(normalize_intraday_minutes(df))
    assert report["status"] == "FAIL"
    assert any(check["name"] == "last_valid_trade_time" and check["status"] == "FAIL" for check in report["checks"])


def test_quality_warns_on_small_missing_minute_gap():
    df = sample_minutes()
    df = df[df["trade_time"] != "2026-06-18 10:00:00"]
    report = quality_report(normalize_intraday_minutes(df))
    assert report["status"] == "WARN"
    coverage = next(check for check in report["checks"] if check["name"] == "minute_window_coverage")
    assert coverage["missing_minute_count"] == 1
