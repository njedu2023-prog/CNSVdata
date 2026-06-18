from pathlib import Path

import pandas as pd

MONEYFLOW_CORE_COLUMNS = [
    "buy_sm_amount",
    "sell_sm_amount",
    "buy_md_amount",
    "sell_md_amount",
    "buy_lg_amount",
    "sell_lg_amount",
    "buy_elg_amount",
    "sell_elg_amount",
    "net_mf_amount",
]


def aggregate_status(checks: list[dict]) -> str:
    if any(check.get("status") == "FAIL" for check in checks):
        return "FAIL"
    if any(check.get("status") == "WARN" for check in checks):
        return "WARN"
    return "PASS"


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


def null_counts(df: pd.DataFrame, columns: list[str]) -> dict:
    counts = {}
    for column in columns:
        if column in df.columns:
            counts[column] = int(df[column].isna().sum())
        else:
            counts[column] = None
    return counts


def numeric_validity_errors(df: pd.DataFrame, columns: list[str]) -> dict:
    errors = {}
    for column in columns:
        if column not in df.columns:
            errors[column] = None
            continue
        numeric = pd.to_numeric(df[column], errors="coerce")
        if column in {"open", "high", "low", "close", "pre_close"}:
            errors[column] = int((numeric <= 0).sum())
        elif column in {"vol", "amount"}:
            errors[column] = int((numeric < 0).sum())
        else:
            errors[column] = int(numeric.isna().sum())
    return errors


def pct_chg_extreme_counts(df: pd.DataFrame) -> dict:
    if "pct_chg" not in df.columns:
        return {"warn_count": 0, "fail_count": 0}
    pct = pd.to_numeric(df["pct_chg"], errors="coerce").abs()
    return {
        "warn_count": int(((pct > 20) & (pct <= 30)).sum()),
        "fail_count": int((pct > 30).sum()),
    }


def invalid_a_share_minute_times(df: pd.DataFrame) -> list[str]:
    if df.empty or "trade_time" not in df.columns:
        return []
    times = pd.to_datetime(df["trade_time"], errors="coerce").dt.strftime("%H:%M:%S")
    valid = ((times >= "09:30:00") & (times <= "11:30:00")) | ((times >= "13:00:00") & (times <= "15:00:00"))
    invalid = df.loc[~valid.fillna(False), "trade_time"].astype(str)
    return invalid.drop_duplicates().sort_values().tolist()


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


def latest_trade_date_of(df: pd.DataFrame, date_col: str = "trade_date") -> str | None:
    if df.empty or date_col not in df.columns:
        return None
    values = df[date_col].dropna().astype(str)
    if values.empty:
        return None
    return str(values.max())


def daily_minute_close_check(daily: pd.DataFrame, minute: pd.DataFrame, trade_date: str, tolerance: float = 0.01) -> dict:
    result = {
        "name": "daily_close_vs_minute_last_close",
        "status": "FAIL",
        "trade_date": trade_date,
        "tolerance": tolerance,
    }
    if daily.empty or minute.empty:
        return {**result, "detail": "daily_or_minute_empty"}
    daily_rows = daily[daily["trade_date"].astype(str) == trade_date]
    minute_rows = minute[minute["trade_date"].astype(str) == trade_date].copy()
    if daily_rows.empty or minute_rows.empty:
        return {**result, "detail": "latest_trade_date_missing"}
    minute_rows["trade_time"] = pd.to_datetime(minute_rows["trade_time"], errors="coerce")
    daily_close = float(daily_rows.sort_values("trade_date").iloc[-1]["close"])
    minute_last_close = float(minute_rows.sort_values("trade_time").iloc[-1]["close"])
    abs_diff = abs(daily_close - minute_last_close)
    return {
        **result,
        "status": "PASS" if abs_diff <= tolerance else "FAIL",
        "daily_close": daily_close,
        "minute_last_close": minute_last_close,
        "abs_diff": round(abs_diff, 6),
        "detail": "close checked",
    }


def daily_minute_amount_check(daily: pd.DataFrame, minute: pd.DataFrame, trade_date: str) -> dict:
    result = {
        "name": "daily_amount_vs_minute_amount_sum",
        "status": "WARN",
        "trade_date": trade_date,
        "detail": "amount_unit_uncertain",
    }
    if daily.empty or minute.empty:
        return {**result, "status": "FAIL", "detail": "daily_or_minute_empty"}
    daily_rows = daily[daily["trade_date"].astype(str) == trade_date]
    minute_rows = minute[minute["trade_date"].astype(str) == trade_date]
    if daily_rows.empty or minute_rows.empty:
        return {**result, "status": "FAIL", "detail": "latest_trade_date_missing"}
    daily_amount = float(daily_rows.sort_values("trade_date").iloc[-1]["amount"])
    minute_amount_sum = float(pd.to_numeric(minute_rows["amount"], errors="coerce").fillna(0).sum())
    if daily_amount <= 0 or minute_amount_sum <= 0:
        return {
            **result,
            "status": "FAIL",
            "daily_amount": daily_amount,
            "minute_amount_sum": minute_amount_sum,
            "detail": "non_positive_amount",
        }
    ratio_direct = abs(daily_amount - minute_amount_sum) / daily_amount
    scaled_minute = minute_amount_sum / 1000
    ratio_scaled = abs(daily_amount - scaled_minute) / daily_amount
    diff_ratio = min(ratio_direct, ratio_scaled)
    if diff_ratio <= 0.03:
        status = "PASS"
        detail = "amount unit checked"
    elif diff_ratio <= 0.08:
        status = "WARN"
        detail = "amount diff within warning range"
    else:
        status = "WARN"
        detail = "amount_unit_uncertain"
    return {
        **result,
        "status": status,
        "daily_amount": daily_amount,
        "minute_amount_sum": minute_amount_sum,
        "diff_ratio": round(diff_ratio, 6),
        "detail": detail,
    }


def moneyflow_effective_check(df: pd.DataFrame) -> dict:
    result = {"name": "moneyflow_effective", "status": "PASS"}
    missing = missing_columns(df, MONEYFLOW_CORE_COLUMNS)
    if missing:
        return {**result, "status": "FAIL", "missing_columns": missing}
    core = df[MONEYFLOW_CORE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if core.isna().all().all():
        return {**result, "status": "FAIL", "detail": "all_core_fields_null"}
    all_zero_by_row = core.fillna(0).eq(0).all(axis=1)
    if bool(all_zero_by_row.tail(3).all()) and len(all_zero_by_row) >= 3:
        return {**result, "status": "FAIL", "detail": "last_3_rows_all_zero"}
    if bool(all_zero_by_row.tail(1).any()):
        return {**result, "status": "WARN", "detail": "latest_row_all_zero"}
    return {**result, "detail": "core fields effective"}
