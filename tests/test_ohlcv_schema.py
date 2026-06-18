import pandas as pd

from cnsvdata.validators import missing_columns, ohlc_errors


def test_missing_columns_reports_schema_gap():
    df = pd.DataFrame({"open": [1], "high": [2]})
    assert missing_columns(df, ["open", "high", "low"]) == ["low"]


def test_ohlc_errors_detects_invalid_bar():
    df = pd.DataFrame({"open": [10], "high": [9], "low": [8], "close": [10]})
    assert ohlc_errors(df) == 1
