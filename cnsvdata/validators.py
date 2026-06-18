from pathlib import Path

import pandas as pd


def missing_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [column for column in required if column not in df.columns]


def duplicate_count(df: pd.DataFrame, columns: list[str]) -> int:
    if df.empty or missing_columns(df, columns):
        return 0
    return int(df.duplicated(subset=columns).sum())


def ohlc_errors(df: pd.DataFrame) -> int:
    required = ["open", "high", "low", "close"]
    if missing_columns(df, required):
        return len(df)
    invalid = (
        (df["high"] < df["open"])
        | (df["high"] < df["close"])
        | (df["low"] > df["open"])
        | (df["low"] > df["close"])
        | (df["high"] < df["low"])
    )
    return int(invalid.sum())


def expected_a_share_minutes(trade_date: str) -> pd.DatetimeIndex:
    morning = pd.date_range(f"{trade_date} 09:30:00", f"{trade_date} 11:30:00", freq="1min")
    afternoon = pd.date_range(f"{trade_date} 13:00:00", f"{trade_date} 15:00:00", freq="1min")
    return morning.append(afternoon)


def minute_coverage(df: pd.DataFrame) -> dict:
    if df.empty or "trade_time" not in df.columns or "trade_date" not in df.columns:
        return {
            "expected_minutes": 0,
            "actual_minutes": 0,
            "missing_minutes": [],
            "duplicate_minutes": 0,
            "coverage_ratio": 0,
        }

    work = df.copy()
    work["trade_time"] = pd.to_datetime(work["trade_time"])
    missing = []
    expected_total = 0
    for trade_date in sorted(work["trade_date"].astype(str).unique()):
        expected = expected_a_share_minutes(trade_date)
        expected_total += len(expected)
        actual = set(work.loc[work["trade_date"].astype(str) == trade_date, "trade_time"])
        missing.extend(ts.strftime("%Y-%m-%d %H:%M:%S") for ts in expected if ts not in actual)

    actual_minutes = int(work["trade_time"].nunique())
    coverage_ratio = actual_minutes / expected_total if expected_total else 0
    return {
        "expected_minutes": expected_total,
        "actual_minutes": actual_minutes,
        "missing_minutes": missing,
        "duplicate_minutes": duplicate_count(work, ["trade_time"]),
        "coverage_ratio": round(coverage_ratio, 6),
    }


def parquet_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0
