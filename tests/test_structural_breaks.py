import pandas as pd

from cnsvdata.common import write_parquet


def test_structural_breaks_required_regimes(tmp_path):
    path = tmp_path / "structural_breaks.parquet"
    write_parquet(
        pd.DataFrame({"regime_id": ["legacy_cssc_before_merger", "merger_transition", "combined_cssc_after_merger"]}),
        path,
    )
    regimes = set(pd.read_parquet(path)["regime_id"])
    assert {"legacy_cssc_before_merger", "merger_transition", "combined_cssc_after_merger"} <= regimes
