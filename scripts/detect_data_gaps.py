import pandas as pd

from cnsvdata.common import now_string, write_json
from cnsvdata.paths import PROCESSED_DIR, QUALITY_DIR
from cnsvdata.validators import aggregate_status


def read_parquet_or_none(path):
    if not path.exists():
        return None
    return pd.read_parquet(path)


def open_trade_dates(calendar: pd.DataFrame | None) -> list[str]:
    if calendar is None or calendar.empty or "cal_date" not in calendar.columns:
        return []
    work = calendar.copy()
    if "is_open" in work.columns:
        work = work[pd.to_numeric(work["is_open"], errors="coerce").fillna(0).astype(int) == 1]
    return sorted(work["cal_date"].dropna().astype(str).unique().tolist())


def dates_in(df: pd.DataFrame | None, column: str = "trade_date") -> set[str]:
    if df is None or df.empty or column not in df.columns:
        return set()
    return set(df[column].dropna().astype(str).unique().tolist())


def missing_date_check(name: str, expected: list[str], actual: set[str], latest: str | None, latest_fail: bool, fail_after: int | None = None) -> dict:
    missing = [date for date in expected if date not in actual]
    status = "PASS"
    detail = "no gaps"
    if latest and latest in missing and latest_fail:
        status = "FAIL"
        detail = "latest_trade_date_missing"
    elif fail_after is not None and len(missing) >= fail_after:
        status = "FAIL"
        detail = "too_many_missing_dates"
    elif missing:
        status = "WARN"
        detail = "historical_gaps_detected"
    return {"name": name, "status": status, "missing_dates": missing, "missing_count": len(missing), "detail": detail}


def build_gap_report() -> dict:
    calendar = read_parquet_or_none(PROCESSED_DIR / "trade_calendar.parquet")
    daily = read_parquet_or_none(PROCESSED_DIR / "cnsv_daily.parquet")
    minute = read_parquet_or_none(PROCESSED_DIR / "cnsv_1min.parquet")
    moneyflow = read_parquet_or_none(PROCESSED_DIR / "cnsv_moneyflow.parquet")
    expected = open_trade_dates(calendar)
    latest = expected[-1] if expected else None
    checks = [
        {"name": "trade_calendar_available", "status": "PASS" if expected else "FAIL", "open_trade_dates": len(expected)},
        missing_date_check("daily_missing_trade_dates", expected, dates_in(daily), latest, latest_fail=True),
        missing_date_check("minute_missing_trade_dates", expected, dates_in(minute), latest, latest_fail=True),
        missing_date_check("moneyflow_missing_trade_dates", expected, dates_in(moneyflow), latest, latest_fail=False, fail_after=3),
    ]
    status = aggregate_status(checks)
    return {
        "status": status,
        "generated_at": now_string(),
        "latest_trade_date": latest or "",
        "checks": checks,
    }


def main() -> None:
    payload = build_gap_report()
    write_json(payload, QUALITY_DIR / "data_gaps_latest.json")
    if payload["status"] == "FAIL":
        raise SystemExit("data gaps status is FAIL")


if __name__ == "__main__":
    main()
