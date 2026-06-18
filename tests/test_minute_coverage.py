import pandas as pd

from cnsvdata.validators import expected_a_share_minutes, minute_coverage


def test_expected_a_share_minutes_has_two_sessions():
    minutes = expected_a_share_minutes("2026-06-18")
    assert minutes[0].strftime("%H:%M:%S") == "09:30:00"
    assert minutes[-1].strftime("%H:%M:%S") == "15:00:00"
    assert "12:00:00" not in {item.strftime("%H:%M:%S") for item in minutes}


def test_minute_coverage_counts_duplicates():
    df = pd.DataFrame(
        {
            "trade_time": ["2026-06-18 09:30:00", "2026-06-18 09:30:00"],
            "trade_date": ["2026-06-18", "2026-06-18"],
        }
    )
    report = minute_coverage(df)
    assert report["duplicate_minutes"] == 1
    assert report["actual_minutes"] == 1
