import json
from pathlib import Path

import pandas as pd

from cnsvdata.common import now_string, write_json
from cnsvdata.paths import PROCESSED_DIR, QUALITY_DIR, ROOT
from cnsvdata.validators import aggregate_status, missing_columns

DAILY_REQUIRED = ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"]
MINUTE_REQUIRED = ["ts_code", "trade_time", "trade_date", "open", "high", "low", "close", "vol", "amount"]
MONEYFLOW_REQUIRED = ["ts_code", "trade_date", "net_mf_amount"]


def read_json(path: Path) -> tuple[dict, dict]:
    if not path.exists():
        return {}, {"name": f"read:{path.relative_to(ROOT)}", "status": "FAIL", "detail": "missing"}
    try:
        return json.loads(path.read_text(encoding="utf-8")), {"name": f"read:{path.relative_to(ROOT)}", "status": "PASS"}
    except Exception as exc:
        return {}, {"name": f"read:{path.relative_to(ROOT)}", "status": "FAIL", "detail": str(exc)}


def read_required_parquet(path: Path, required_columns: list[str], label: str) -> tuple[pd.DataFrame | None, list[dict]]:
    checks = []
    if not path.exists():
        return None, [{"name": f"read_{label}", "status": "FAIL", "detail": "missing"}]
    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        return None, [{"name": f"read_{label}", "status": "FAIL", "detail": str(exc)}]
    checks.append({"name": f"read_{label}", "status": "PASS", "rows": int(len(df))})
    missing = missing_columns(df, required_columns)
    checks.append({"name": f"{label}_core_fields", "status": "FAIL" if missing else "PASS", "missing_columns": missing})
    if df.empty:
        checks.append({"name": f"{label}_non_empty", "status": "FAIL", "detail": "empty"})
    return df, checks


def build_smoke_report() -> dict:
    checks = []
    manifest, check = read_json(ROOT / "metadata" / "data_manifest.json")
    checks.append(check)
    quality, check = read_json(QUALITY_DIR / "data_quality_latest.json")
    checks.append(check)
    acceptance, check = read_json(QUALITY_DIR / "acceptance_latest.json")
    checks.append(check)
    for label, payload in (("quality", quality), ("acceptance", acceptance)):
        status = payload.get("status")
        checks.append({"name": f"{label}_not_fail", "status": "FAIL" if status == "FAIL" or status is None else "WARN" if status == "WARN" else "PASS", f"{label}_status": status})

    daily, daily_checks = read_required_parquet(PROCESSED_DIR / "cnsv_daily.parquet", DAILY_REQUIRED, "cnsv_daily")
    minute, minute_checks = read_required_parquet(PROCESSED_DIR / "cnsv_1min.parquet", MINUTE_REQUIRED, "cnsv_1min")
    moneyflow, moneyflow_checks = read_required_parquet(PROCESSED_DIR / "cnsv_moneyflow.parquet", MONEYFLOW_REQUIRED, "cnsv_moneyflow")
    checks.extend(daily_checks + minute_checks + moneyflow_checks)
    latest_trade_date = manifest.get("latest_trade_date") or acceptance.get("latest_trade_date")
    checks.append({"name": "latest_trade_date_available", "status": "PASS" if latest_trade_date else "FAIL", "latest_trade_date": latest_trade_date})

    status = aggregate_status(checks)
    failed = [check for check in checks if check["status"] == "FAIL"]
    warned = [check for check in checks if check["status"] == "WARN"]
    return {
        "status": status,
        "generated_at": now_string(),
        "latest_trade_date": latest_trade_date or "",
        "failed_count": len(failed),
        "warn_count": len(warned),
        "checks": checks,
    }


def main() -> None:
    payload = build_smoke_report()
    write_json(payload, QUALITY_DIR / "downstream_smoke_latest.json")
    if payload["status"] == "FAIL":
        raise SystemExit("downstream smoke status is FAIL")


if __name__ == "__main__":
    main()
