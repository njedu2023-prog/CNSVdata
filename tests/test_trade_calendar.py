import pandas as pd


def test_trade_calendar_next_open_day_uses_open_rows():
    df = pd.DataFrame(
        {
            "cal_date": ["2026-06-18", "2026-06-19", "2026-06-20"],
            "is_open": [1, 1, 0],
            "pretrade_date": ["2026-06-17", "2026-06-18", "2026-06-19"],
            "exchange": ["SSE", "SSE", "SSE"],
        }
    )
    open_days = df.loc[df["is_open"] == 1, "cal_date"].tolist()
    assert max(day for day in open_days if day <= "2026-06-18") == "2026-06-18"
    assert min(day for day in open_days if day > "2026-06-18") == "2026-06-19"
