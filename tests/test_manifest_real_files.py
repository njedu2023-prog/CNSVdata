import pandas as pd

from cnsvdata.common import file_sha256, write_parquet
from scripts.build_data_manifest import date_range_for_df


def test_file_sha256_and_manifest_item_shape(tmp_path):
    path = tmp_path / "sample.parquet"
    df = pd.DataFrame({"trade_date": ["2026-06-18"], "close": [36.14]})
    write_parquet(df, path)
    digest = file_sha256(path)
    assert len(digest) == 64
    min_date, max_date = date_range_for_df(df)
    item = {
        "path": "data/processed/sample.parquet",
        "exists": True,
        "rows": len(df),
        "columns": list(df.columns),
        "sha256": digest,
        "file_size": path.stat().st_size,
        "status": "PASS",
    }
    assert min_date == "2026-06-18"
    assert max_date == "2026-06-18"
    assert {"path", "exists", "rows", "columns", "sha256", "file_size", "status"} <= set(item)
