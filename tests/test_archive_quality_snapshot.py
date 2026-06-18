from scripts.archive_quality_snapshot import archive_snapshot


def test_archive_snapshot_returns_copy_report():
    report = archive_snapshot()
    assert "copied" in report
    assert "missing" in report
    assert report["date"]
