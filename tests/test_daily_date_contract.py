from cnsvdata.daily import _iso_date


def test_daily_metadata_dates_are_iso_8601():
    assert _iso_date("20260714") == "2026-07-14"
    assert _iso_date("2026-07-14") == "2026-07-14"
    assert _iso_date(20260714) == "2026-07-14"
    assert _iso_date("") is None
