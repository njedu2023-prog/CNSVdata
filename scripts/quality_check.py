import json

import pandas as pd

from cnsvdata.common import load_yaml, now_string, write_json
from cnsvdata.paths import METADATA_DIR, PROCESSED_DIR, QUALITY_DIR, ROOT
from cnsvdata.validators import (
    aggregate_status,
    daily_minute_amount_check,
    daily_minute_close_check,
    duplicate_count,
    field_contract_checks,
    invalid_a_share_minute_times,
    latest_trade_date_of,
    minute_coverage,
    missing_columns,
    moneyflow_effective_check,
    null_counts,
    numeric_validity_errors,
    ohlc_errors,
    pct_chg_extreme_counts,
)

DAILY_CORE = ["ts_code", "trade_date", "open", "high", "low", "close", "pre_close", "vol", "amount"]
MINUTE_CORE = ["ts_code", "trade_time", "trade_date", "time", "open", "high", "low", "close", "vol", "amount"]
MONEYFLOW_CORE = ["ts_code", "trade_date", "net_mf_amount"]


def read_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_parquet(path, required_columns: list[str], duplicate_key: list[str] | None = None, ohlc: bool = False) -> tuple[list[dict], pd.DataFrame | None]:
    checks = []
    if not path.exists():
        return [{"name": f"{path.name}_exists", "status": "FAIL", "detail": "missing file"}], None
    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        return [{"name": f"{path.name}_readable", "status": "FAIL", "detail": str(exc)}], None

    checks.append({"name": f"{path.name}_exists", "status": "PASS", "rows": int(len(df))})
    missing = missing_columns(df, required_columns)
    checks.append({"name": f"{path.name}_schema", "status": "FAIL" if missing else "PASS", "missing_columns": missing})
    if duplicate_key:
        count = duplicate_count(df, duplicate_key)
        checks.append({"name": f"{path.name}_duplicates", "status": "FAIL" if count else "PASS", "count": count})
    if ohlc:
        count = ohlc_errors(df)
        checks.append({"name": f"{path.name}_ohlc", "status": "FAIL" if count else "PASS", "count": count})
    return checks, df


def add_null_check(checks: list[dict], name: str, df: pd.DataFrame | None, core_columns: list[str]) -> None:
    if df is None:
        return
    counts = null_counts(df, core_columns)
    bad = {column: count for column, count in counts.items() if count}
    checks.append({"name": f"{name}_core_nulls", "status": "FAIL" if bad else "PASS", "null_counts": counts})


def add_numeric_check(checks: list[dict], name: str, df: pd.DataFrame | None) -> None:
    if df is None:
        return
    counts = numeric_validity_errors(df, ["open", "high", "low", "close", "pre_close", "vol", "amount"])
    bad = {column: count for column, count in counts.items() if count}
    checks.append({"name": f"{name}_numeric_validity", "status": "FAIL" if bad else "PASS", "error_counts": counts})
    pct = pct_chg_extreme_counts(df)
    checks.append(
        {
            "name": f"{name}_pct_chg_extreme",
            "status": "FAIL" if pct["fail_count"] else "WARN" if pct["warn_count"] else "PASS",
            **pct,
        }
    )


def latest_trade_date_consistency(daily, minute, moneyflow) -> dict:
    metadata_latest = read_json(METADATA_DIR / "latest_trade_date.json").get("latest_trade_date")
    daily_max = latest_trade_date_of(daily) if daily is not None else None
    minute_max = latest_trade_date_of(minute) if minute is not None else None
    moneyflow_max = latest_trade_date_of(moneyflow) if moneyflow is not None else None
    status = "PASS"
    detail = "latest trade dates checked"
    if not metadata_latest or daily_max != metadata_latest:
        status = "FAIL"
        detail = "daily or metadata latest date mismatch"
    elif minute is not None and minute_max != metadata_latest:
        status = "WARN"
        detail = "minute latest date mismatch"
    elif moneyflow is not None and moneyflow_max != metadata_latest:
        status = "WARN"
        detail = "moneyflow latest date mismatch"
    return {
        "name": "latest_trade_date_consistency",
        "status": status,
        "metadata_latest_trade_date": metadata_latest,
        "daily_max_trade_date": daily_max,
        "minute_max_trade_date": minute_max,
        "moneyflow_max_trade_date": moneyflow_max,
        "detail": detail,
    }


def main() -> None:
    schemas = load_yaml("schema.yml")
    contract = load_yaml("data_contract.yml")["contract"]
    field_contract = load_yaml("field_contract.yml")["contract"]
    checks = []

    for relative in contract["required_files"]:
        path = ROOT / relative
        if relative == "data/quality/data_quality_latest.json":
            checks.append({"name": f"required_file:{relative}", "status": "PASS", "detail": "current_output"})
        else:
            checks.append({"name": f"required_file:{relative}", "status": "PASS" if path.exists() else "FAIL", "detail": "present" if path.exists() else "missing"})

    checks_calendar, calendar = check_parquet(PROCESSED_DIR / "trade_calendar.parquet", list(schemas["trade_calendar_schema"].keys()), duplicate_key=["cal_date"])
    checks_daily, daily = check_parquet(PROCESSED_DIR / "cnsv_daily.parquet", list(schemas["daily_schema"].keys()), duplicate_key=["trade_date"], ohlc=True)
    checks_minute, minute = check_parquet(PROCESSED_DIR / "cnsv_1min.parquet", list(schemas["minute_schema"].keys()), duplicate_key=["trade_time"], ohlc=True)
    checks_moneyflow, moneyflow = check_parquet(PROCESSED_DIR / "cnsv_moneyflow.parquet", list(schemas["moneyflow_schema"].keys()), duplicate_key=["trade_date"])
    checks.extend(checks_calendar + checks_daily + checks_minute + checks_moneyflow)
    checks.extend(check_parquet(PROCESSED_DIR / "corporate_actions.parquet", list(schemas["corporate_actions_schema"].keys()))[0])
    checks.extend(check_parquet(PROCESSED_DIR / "structural_breaks.parquet", list(schemas["structural_breaks_schema"].keys()))[0])
    frames = {
        "trade_calendar": calendar,
        "cnsv_daily": daily,
        "cnsv_1min": minute,
        "cnsv_moneyflow": moneyflow,
    }
    for dataset_name, dataset_contract in field_contract["datasets"].items():
        checks.extend(field_contract_checks(frames.get(dataset_name), dataset_name, dataset_contract))

    add_null_check(checks, "daily", daily, DAILY_CORE)
    add_null_check(checks, "minute", minute, MINUTE_CORE)
    add_null_check(checks, "moneyflow", moneyflow, MONEYFLOW_CORE)
    add_numeric_check(checks, "daily", daily)
    add_numeric_check(checks, "minute", minute)

    if minute is not None:
        coverage = minute_coverage(minute)
        coverage_status = "PASS" if coverage["coverage_ratio"] >= 0.99 and coverage["duplicate_minutes"] == 0 else "WARN"
        write_json(coverage, QUALITY_DIR / "missing_minutes_report.json")
        checks.append({"name": "minute_coverage", "status": coverage_status, **coverage})
        invalid_times = invalid_a_share_minute_times(minute)
        checks.append(
            {
                "name": "minute_trading_session",
                "status": "FAIL" if len(invalid_times) > 3 else "WARN" if invalid_times else "PASS",
                "invalid_count": len(invalid_times),
                "invalid_examples": invalid_times[:20],
            }
        )

    checks.append(latest_trade_date_consistency(daily, minute, moneyflow))
    latest = read_json(METADATA_DIR / "latest_trade_date.json").get("latest_trade_date")
    if latest and daily is not None and minute is not None:
        checks.append(daily_minute_close_check(daily, minute, latest))
        checks.append(daily_minute_amount_check(daily, minute, latest))
    if moneyflow is not None:
        checks.append(moneyflow_effective_check(moneyflow))

    if (QUALITY_DIR / "minute_aggregation_check.json").exists():
        agg = read_json(QUALITY_DIR / "minute_aggregation_check.json")
        checks.append({"name": "minute_aggregation_check", "status": agg.get("status", "FAIL"), "detail": agg.get("checks", [])})

    status = aggregate_status(checks)
    failed = [check for check in checks if check["status"] == "FAIL"]
    warned = [check for check in checks if check["status"] == "WARN"]
    payload = {
        "status": status,
        "generated_at": now_string(),
        "failed_count": len(failed),
        "warn_count": len(warned),
        "checks": checks,
    }
    write_json(payload, QUALITY_DIR / "data_quality_latest.json")
    write_json(
        {
            "generated_at": payload["generated_at"],
            "status": status,
            "failed_count": len(failed),
            "warn_count": len(warned),
        },
        QUALITY_DIR / "latest_run_summary.json",
    )
    if status == "FAIL":
        raise SystemExit("data quality status is FAIL")


if __name__ == "__main__":
    main()
