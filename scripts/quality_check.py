import json

import pandas as pd

from cnsvdata.common import load_yaml, now_string, write_json
from cnsvdata.paths import METADATA_DIR, PROCESSED_DIR, QUALITY_DIR, ROOT
from cnsvdata.validators import duplicate_count, minute_coverage, missing_columns, ohlc_errors


def check_parquet(path, required_columns: list[str], duplicate_key: list[str] | None = None, ohlc: bool = False) -> list[dict]:
    checks = []
    if not path.exists():
        return [{"name": f"{path.name}_exists", "status": "FAIL", "detail": "missing file"}]
    df = pd.read_parquet(path)
    checks.append({"name": f"{path.name}_exists", "status": "PASS", "rows": int(len(df))})
    missing = missing_columns(df, required_columns)
    checks.append(
        {
            "name": f"{path.name}_schema",
            "status": "FAIL" if missing else "PASS",
            "missing_columns": missing,
        }
    )
    if duplicate_key:
        count = duplicate_count(df, duplicate_key)
        checks.append({"name": f"{path.name}_duplicates", "status": "FAIL" if count else "PASS", "count": count})
    if ohlc:
        count = ohlc_errors(df)
        checks.append({"name": f"{path.name}_ohlc", "status": "FAIL" if count else "PASS", "count": count})
    return checks


def main() -> None:
    schemas = load_yaml("schema.yml")
    contract = load_yaml("data_contract.yml")["contract"]
    checks = []

    for relative in contract["required_files"]:
        path = ROOT / relative
        checks.append(
            {
                "name": f"required_file:{relative}",
                "status": "PASS" if path.exists() else "FAIL",
                "detail": "present" if path.exists() else "missing",
            }
        )

    checks.extend(
        check_parquet(
            PROCESSED_DIR / "trade_calendar.parquet",
            list(schemas["trade_calendar_schema"].keys()),
            duplicate_key=["cal_date"],
        )
    )
    checks.extend(
        check_parquet(
            PROCESSED_DIR / "cnsv_daily.parquet",
            list(schemas["daily_schema"].keys()),
            duplicate_key=["trade_date"],
            ohlc=True,
        )
    )
    checks.extend(
        check_parquet(
            PROCESSED_DIR / "cnsv_1min.parquet",
            list(schemas["minute_schema"].keys()),
            duplicate_key=["trade_time"],
            ohlc=True,
        )
    )
    checks.extend(
        check_parquet(
            PROCESSED_DIR / "cnsv_moneyflow.parquet",
            list(schemas["moneyflow_schema"].keys()),
            duplicate_key=["trade_date"],
        )
    )
    checks.extend(check_parquet(PROCESSED_DIR / "corporate_actions.parquet", list(schemas["corporate_actions_schema"].keys())))
    checks.extend(check_parquet(PROCESSED_DIR / "structural_breaks.parquet", list(schemas["structural_breaks_schema"].keys())))

    if (PROCESSED_DIR / "cnsv_1min.parquet").exists():
        coverage = minute_coverage(pd.read_parquet(PROCESSED_DIR / "cnsv_1min.parquet"))
        coverage_status = "PASS" if coverage["coverage_ratio"] >= 0.99 and coverage["duplicate_minutes"] == 0 else "WARN"
        write_json(coverage, QUALITY_DIR / "missing_minutes_report.json")
        checks.append({"name": "minute_coverage", "status": coverage_status, **coverage})

    if (QUALITY_DIR / "minute_aggregation_check.json").exists():
        agg = json.loads((QUALITY_DIR / "minute_aggregation_check.json").read_text(encoding="utf-8"))
        checks.append({"name": "minute_aggregation_check", "status": agg.get("status", "FAIL"), "detail": agg.get("checks", [])})

    failed = [check for check in checks if check["status"] == "FAIL"]
    warned = [check for check in checks if check["status"] == "WARN"]
    status = "FAIL" if failed else "WARN" if warned else "PASS"
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
