import pandas as pd

from cnsvdata.validators import duplicate_count


def test_duplicate_count_by_trade_time():
    df = pd.DataFrame({"trade_time": ["2026-06-18 09:30:00", "2026-06-18 09:30:00"]})
    assert duplicate_count(df, ["trade_time"]) == 1
