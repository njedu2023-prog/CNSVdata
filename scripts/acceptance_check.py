import json
from pathlib import Path

import pandas as pd

from cnsvdata.common import load_yaml, now_string, write_json
from cnsvdata.paths import METADATA_DIR, PROCESSED_DIR, QUALITY_DIR, ROOT
from cnsvdata.validators import (
    aggregate_status,
    daily_minute_amount_check,
    daily_minute_close_check,
    field_contract_checks,
    latest_trade_date_of,
    missing_columns,
    moneyflow_effective_check,
)

CORE_PARQUET_FILES = {
    "data/processed/trade_calendar.parquet",
    "data/processed/cnsv_daily.parquet",
    "data/processed/cnsv_1min.parquet",
    "data/processed/cnsv_5min.parquet",
    "data/processed/cnsv_15min.parquet",
    "data/processed/cnsv_30min.parquet",
    "data/processed/cnsv_60min.parquet",
    "data/processed/cnsv_moneyflow.parquet",
}
EMPTY_ALLOWED = {
    "data/processed/corporate_actions.parquet",
    "data/processed/structural_breaks.parquet",
}
MANIFEST_ITEM_FIELDS = ["path", "exists", "rows", "columns", "sha256", "file_size", "updated_at", "status"]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def required_file_checks(required_files: list[str]) -> list[dict]:
    checks = []
    for relative in required_files:
        path = ROOT / relative
        checks.append({"name": f"required_file:{relative}", "status": "PASS" if path.exists() else "FAIL", "detail": "present" if path.exists() else "missing"})
    return checks


def parquet_readability_check(relative: str) -> tuple[dict, pd.DataFrame | None]:
    path = ROOT / relative
    if not path.exists():
        return {"name": f"parquet_readable:{path.name}", "status": "FAIL", "detail": "missing"}, None
    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        return {"name": f"parquet_readable:{path.name}", "status": "FAIL", "detail": str(exc)}, None
    status = "PASS"
    detail = "readable"
    empty_allowed = relative in EMPTY_ALLOWED
    if len(df.columns) == 0:
        status = "FAIL"
        detail = "no columns"
    elif len(df) == 0 and relative in CORE_PARQUET_FILES:
        status = "FAIL"
        detail = "empty core file"
    elif len(df) == 0 and empty_allowed:
        status = "WARN"
        detail = "empty_allowed"
    return {
        "name": f"parquet_readable:{path.name}",
        "status": status,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "empty_allowed": empty_allowed,
        "detail": detail,
    }, df


def latest_trade_date_check(latest: str | None, daily, minute, moneyflow) -> dict:
    daily_max = latest_trade_date_of(daily) if daily is not None else None
    minute_max = latest_trade_date_of(minute) if minute is not None else None
    moneyflow_max = latest_trade_date_of(moneyflow) if moneyflow is not None else None
    status = "PASS"
    detail = "latest trade dates checked"
    if not latest or daily_max != latest:
        status = "FAIL"
        detail = "daily latest date mismatch"
    elif minute_max != latest:
        status = "FAIL"
        detail = "minute latest date mismatch"
    elif moneyflow_max != latest:
        status = "WARN"
        detail = "moneyflow latest date mismatch"
    return {
        "name": "latest_trade_date_consistency",
        "status": status,
        "metadata_latest_trade_date": latest,
        "daily_max_trade_date": daily_max,
        "minute_max_trade_date": minute_max,
        "moneyflow_max_trade_date": moneyflow_max,
        "detail": detail,
    }


def manifest_check(required_files: list[str]) -> tuple[list[dict], dict]:
    checks = []
    path = METADATA_DIR / "data_manifest.json"
    manifest = read_json(path)
    checks.append({"name": "manifest_exists", "status": "PASS" if path.exists() else "FAIL"})
    for field in ("snapshot_id", "generated_at", "latest_trade_date", "files"):
        checks.append({"name": f"manifest_field:{field}", "status": "PASS" if manifest.get(field) else "FAIL"})
    file_items = manifest.get("files", []) if isinstance(manifest.get("files"), list) else []
    manifest_paths = {item.get("path") for item in file_items}
    missing_from_manifest = [relative for relative in required_files if relative not in manifest_paths]
    checks.append({"name": "manifest_covers_required_files", "status": "FAIL" if missing_from_manifest else "PASS", "missing": missing_from_manifest})
    for item in file_items:
        missing_fields = [field for field in MANIFEST_ITEM_FIELDS if field not in item]
        checks.append({"name": f"manifest_item:{item.get('path', '<missing>')}", "status": "FAIL" if missing_fields else "PASS", "missing_fields": missing_fields})
    return checks, manifest


def quality_status_check() -> dict:
    path = QUALITY_DIR / "data_quality_latest.json"
    payload = read_json(path)
    status = payload.get("status")
    if not path.exists() or status not in {"PASS", "WARN", "FAIL"}:
        return {"name": "quality_status", "status": "FAIL", "detail": "missing_or_invalid_quality"}
    return {"name": "quality_status", "status": status, "quality_status": status}


def data_gaps_status_check() -> dict:
    path = QUALITY_DIR / "data_gaps_latest.json"
    payload = read_json(path)
    status = payload.get("status")
    if not path.exists() or status not in {"PASS", "WARN", "FAIL"}:
        return {"name": "data_gaps_status", "status": "FAIL", "detail": "missing_or_invalid_data_gaps"}
    return {
        "name": "data_gaps_status",
        "status": status,
        "data_gaps_status": status,
        "unresolved_gaps": len(payload.get("unresolved_gaps", []) or []),
    }


def build_acceptance_report() -> dict:
    contract = load_yaml("data_contract.yml")["contract"]
    field_contract = load_yaml("field_contract.yml")["contract"]
    required_files = contract["required_files"]
    latest_payload = read_json(METADATA_DIR / "latest_trade_date.json")
    latest = latest_payload.get("latest_trade_date")
    checks = []
    frames = {}

    checks.extend(required_file_checks(required_files))
    for relative in required_files:
        if relative.endswith(".parquet"):
            check, df = parquet_readability_check(relative)
            checks.append(check)
            frames[relative] = df

    checks.append(latest_trade_date_check(latest, frames.get("data/processed/cnsv_daily.parquet"), frames.get("data/processed/cnsv_1min.parquet"), frames.get("data/processed/cnsv_moneyflow.parquet")))
    daily = frames.get("data/processed/cnsv_daily.parquet")
    minute = frames.get("data/processed/cnsv_1min.parquet")
    moneyflow = frames.get("data/processed/cnsv_moneyflow.parquet")
    if latest and daily is not None and minute is not None:
        checks.append(daily_minute_close_check(daily, minute, latest))
        checks.append(daily_minute_amount_check(daily, minute, latest))
    if moneyflow is not None:
        checks.append(moneyflow_effective_check(moneyflow))

    manifest_checks, manifest = manifest_check(required_files)
    checks.extend(manifest_checks)
    dataset_by_path = {spec.get("path"): name for name, spec in field_contract["datasets"].items()}
    for relative, dataset_name in dataset_by_path.items():
        checks.extend(field_contract_checks(frames.get(relative), dataset_name, field_contract["datasets"][dataset_name]))
    checks.append(quality_status_check())
    checks.append(data_gaps_status_check())

    status = aggregate_status(checks)
    failed = [check for check in checks if check["status"] == "FAIL"]
    warned = [check for check in checks if check["status"] == "WARN"]
    return {
        "status": status,
        "generated_at": now_string(),
        "snapshot_id": manifest.get("snapshot_id", ""),
        "latest_trade_date": latest or manifest.get("latest_trade_date", ""),
        "failed_count": len(failed),
        "warn_count": len(warned),
        "checks": checks,
    }


def main() -> None:
    payload = build_acceptance_report()
    write_json(payload, QUALITY_DIR / "acceptance_latest.json")
    if payload["status"] == "FAIL":
        raise SystemExit("acceptance status is FAIL")


if __name__ == "__main__":
    main()
