import json

import pandas as pd

from cnsvdata.common import now_string, write_json
from cnsvdata.paths import METADATA_DIR, PROCESSED_DIR, QUALITY_DIR
from cnsvdata.validators import aggregate_status, minute_coverage


def read_json_or_empty(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def latest_trade_date_from_metadata() -> str | None:
    value = read_json_or_empty(METADATA_DIR / "latest_trade_date.json").get("latest_trade_date")
    return str(value) if value else None


def bounded_expected_dates(calendar: pd.DataFrame | None, latest: str | None) -> list[str]:
    dates = open_trade_dates(calendar)
    if not latest:
        return dates
    return [date for date in dates if date <= latest]


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


def lag_tolerant_missing_date_check(name: str, expected: list[str], actual: set[str], fail_consecutive: int = 2) -> dict:
    missing = [date for date in expected if date not in actual]
    status = "PASS"
    detail = "no gaps"
    recent = expected[-fail_consecutive:] if fail_consecutive else []
    if recent and all(date in missing for date in recent):
        status = "FAIL"
        detail = "consecutive_recent_missing_dates"
    elif missing:
        status = "WARN"
        detail = "latest_or_historical_gaps_detected"
    return {"name": name, "status": status, "missing_dates": missing, "missing_count": len(missing), "detail": detail}


def consecutive_missing_lag(expected: list[str], actual: set[str]) -> int:
    count = 0
    for date in reversed(expected):
        if date in actual:
            break
        count += 1
    return count


def latest_minute_coverage(minute: pd.DataFrame | None, latest: str | None) -> dict:
    if minute is None or not latest or "trade_date" not in minute.columns:
        return {"coverage_ratio": 0, "missing_minutes": [], "latest_trade_date_present": False}
    latest_rows = minute[minute["trade_date"].astype(str) == latest]
    if latest_rows.empty:
        return {"coverage_ratio": 0, "missing_minutes": [], "latest_trade_date_present": False}
    coverage = minute_coverage(latest_rows)
    return {
        "coverage_ratio": coverage["coverage_ratio"],
        "missing_minutes": coverage["missing_minutes"],
        "latest_trade_date_present": True,
    }


def unresolved_gap(name: str, status: str, missing_dates: list[str], reason: str, impact: str) -> dict | None:
    if not missing_dates:
        return None
    return {
        "dataset": name,
        "status": status,
        "missing_dates": missing_dates,
        "missing_count": len(missing_dates),
        "reason": reason,
        "impact": impact,
    }


def suggested_backfill_commands(daily: dict, minute: dict, moneyflow: dict) -> list[str]:
    commands = []
    if daily.get("missing_trade_dates"):
        commands.append("python scripts/backfill_missing_data.py --from-gap-report")
        commands.append("python scripts/backfill_missing_data.py --daily")
    if minute.get("missing_trade_dates") or minute.get("missing_minutes"):
        commands.append("python scripts/backfill_missing_data.py --minute")
    if moneyflow.get("missing_trade_dates"):
        commands.append("python scripts/backfill_missing_data.py --moneyflow")
    return list(dict.fromkeys(commands))


def build_gap_report() -> dict:
    calendar = read_parquet_or_none(PROCESSED_DIR / "trade_calendar.parquet")
    daily = read_parquet_or_none(PROCESSED_DIR / "cnsv_daily.parquet")
    minute = read_parquet_or_none(PROCESSED_DIR / "cnsv_1min.parquet")
    moneyflow = read_parquet_or_none(PROCESSED_DIR / "cnsv_moneyflow.parquet")
    latest = latest_trade_date_from_metadata()
    expected = bounded_expected_dates(calendar, latest)
    latest = latest or (expected[-1] if expected else None)
    daily_dates = dates_in(daily)
    minute_dates = dates_in(minute)
    moneyflow_dates = dates_in(moneyflow)
    daily_check = missing_date_check("daily_missing_trade_dates", expected, daily_dates, latest, latest_fail=True)
    minute_check = missing_date_check("minute_missing_trade_dates", expected, minute_dates, latest, latest_fail=True)
    moneyflow_check = lag_tolerant_missing_date_check("moneyflow_missing_trade_dates", expected, moneyflow_dates, fail_consecutive=3)
    coverage = minute_coverage(minute) if minute is not None else {"coverage_ratio": 0, "missing_minutes": []}
    latest_coverage = latest_minute_coverage(minute, latest)
    moneyflow_lag = consecutive_missing_lag(expected, moneyflow_dates)

    daily_report = {
        "status": daily_check["status"],
        "missing_trade_dates": daily_check["missing_dates"],
        "missing_count": daily_check["missing_count"],
        "latest_trade_date_present": bool(latest and latest in daily_dates),
        "impact": "historical gaps can affect backtests and training" if daily_check["missing_dates"] else "",
    }
    minute_report = {
        "status": minute_check["status"],
        "missing_trade_dates": minute_check["missing_dates"],
        "missing_count": minute_check["missing_count"],
        "missing_minutes": coverage.get("missing_minutes", []),
        "coverage_ratio": coverage.get("coverage_ratio", 0),
        "latest_trade_date_present": latest_coverage["latest_trade_date_present"],
        "latest_trade_date_coverage": latest_coverage,
        "impact": "historical minute gaps can affect intraday backtests and training" if minute_check["missing_dates"] else "",
    }
    moneyflow_report = {
        "status": moneyflow_check["status"],
        "missing_trade_dates": moneyflow_check["missing_dates"],
        "missing_count": moneyflow_check["missing_count"],
        "latest_lag_trading_days": moneyflow_lag,
        "latest_trade_date_present": bool(latest and latest in moneyflow_dates),
        "impact": "moneyflow WARN means it can only be used as a low confidence auxiliary factor" if moneyflow_check["missing_dates"] else "",
    }
    unresolved = [
        item
        for item in [
            unresolved_gap("daily", daily_check["status"], daily_check["missing_dates"], "source historical gaps or pending backfill", daily_report["impact"]),
            unresolved_gap("minute", minute_check["status"], minute_check["missing_dates"], "Tushare minute data may have a limited recent coverage window", minute_report["impact"]),
            unresolved_gap("moneyflow", moneyflow_check["status"], moneyflow_check["missing_dates"], "source historical gaps or normal moneyflow lag", moneyflow_report["impact"]),
        ]
        if item
    ]
    checks = [
        {"name": "trade_calendar_available", "status": "PASS" if expected else "FAIL", "open_trade_dates": len(expected)},
        daily_check,
        minute_check,
        {"name": "minute_missing_minutes", "status": "WARN" if coverage.get("missing_minutes") else "PASS", "missing_minutes": coverage.get("missing_minutes", []), "coverage_ratio": coverage.get("coverage_ratio", 0)},
        moneyflow_check,
    ]
    status = aggregate_status(checks)
    return {
        "status": status,
        "generated_at": now_string(),
        "latest_trade_date": latest or "",
        "checks": checks,
        "daily_missing_trade_dates": daily_check,
        "minute_missing_trade_dates": minute_check,
        "minute_missing_minutes": checks[3],
        "moneyflow_missing_trade_dates": moneyflow_check,
        "daily": daily_report,
        "minute": minute_report,
        "moneyflow": moneyflow_report,
        "unresolved_gaps": unresolved,
        "suggested_backfill_commands": suggested_backfill_commands(daily_report, minute_report, moneyflow_report),
    }


def main() -> None:
    payload = build_gap_report()
    write_json(payload, QUALITY_DIR / "data_gaps_latest.json")
    if payload["status"] == "FAIL":
        raise SystemExit("data gaps status is FAIL")


if __name__ == "__main__":
    main()
