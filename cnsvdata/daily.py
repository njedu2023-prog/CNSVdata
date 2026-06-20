from __future__ import annotations

from pathlib import Path

import pandas as pd

from cnsvdata.common import file_sha256, now_string, write_json
from cnsvdata.paths import DATA_DIR, METADATA_DIR, PROCESSED_DIR, QUALITY_DIR, ROOT

DAILY_DIR = DATA_DIR / "daily"
DAILY_RAW_DIR = DAILY_DIR / "raw"
DAILY_PROCESSED_DIR = DAILY_DIR / "processed"
DAILY_PREVIEW_DIR = DAILY_DIR / "preview"
DAILY_REFERENCE_DIR = DAILY_DIR / "reference"
DAILY_QUALITY_DIR = QUALITY_DIR / "daily"
DAILY_METADATA_DIR = METADATA_DIR / "daily"

DAILY_CORE_FILES = {
    "cnsv_daily": DAILY_PROCESSED_DIR / "cnsv_daily.parquet",
    "cnsv_moneyflow": DAILY_PROCESSED_DIR / "cnsv_moneyflow.parquet",
    "corporate_actions": DAILY_PROCESSED_DIR / "corporate_actions.parquet",
    "structural_breaks": DAILY_PROCESSED_DIR / "structural_breaks.parquet",
    "trade_calendar": DAILY_PROCESSED_DIR / "trade_calendar.parquet",
}

LEGACY_DAILY_CORE_FILES = {
    "cnsv_daily": PROCESSED_DIR / "cnsv_daily.parquet",
    "cnsv_moneyflow": PROCESSED_DIR / "cnsv_moneyflow.parquet",
    "corporate_actions": PROCESSED_DIR / "corporate_actions.parquet",
    "structural_breaks": PROCESSED_DIR / "structural_breaks.parquet",
    "trade_calendar": PROCESSED_DIR / "trade_calendar.parquet",
}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _file_entry(name: str, canonical: Path, legacy: Path) -> dict:
    source = canonical if canonical.exists() else legacy
    exists = source.exists()
    return {
        "name": name,
        "canonical_path": _display_path(canonical),
        "legacy_path": _display_path(legacy),
        "path": _display_path(source) if exists else _display_path(canonical),
        "exists": exists,
        "sha256": file_sha256(source) if exists else "",
        "size_bytes": source.stat().st_size if exists else 0,
        "legacy_compatibility": source == legacy and exists,
        "canonical_line": "daily",
    }


def _read_first_existing(name: str) -> pd.DataFrame:
    for path in (DAILY_CORE_FILES[name], LEGACY_DAILY_CORE_FILES[name]):
        if path.exists():
            return pd.read_parquet(path)
    return pd.DataFrame()


def _daily_trade_dates() -> tuple[str | None, str | None]:
    daily = _read_first_existing("cnsv_daily")
    latest = None
    if not daily.empty and "trade_date" in daily.columns:
        dates = sorted(daily["trade_date"].dropna().astype(str).str[:10].str.replace("-", "", regex=False).unique())
        latest = dates[-1] if dates else None
    calendar = _read_first_existing("trade_calendar")
    next_trade_date = None
    if latest and not calendar.empty:
        column = "cal_date" if "cal_date" in calendar.columns else "trade_date"
        if column in calendar.columns:
            cal = calendar.copy()
            if "is_open" in cal.columns:
                cal = cal[pd.to_numeric(cal["is_open"], errors="coerce") == 1]
            dates = sorted(cal[column].dropna().astype(str).str[:10].str.replace("-", "", regex=False).unique())
            next_dates = [date for date in dates if date > latest]
            next_trade_date = next_dates[0] if next_dates else None
    return latest, next_trade_date


def build_daily_manifest() -> dict:
    DAILY_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        _file_entry(name, DAILY_CORE_FILES[name], LEGACY_DAILY_CORE_FILES[name])
        for name in DAILY_CORE_FILES
    ]
    manifest = {
        "line": "daily",
        "repo": "CNSVdata",
        "generated_at": now_string(),
        "manifest_path": "metadata/daily/daily_manifest.json",
        "quality_path": "data/quality/daily/daily_quality_latest.json",
        "legacy_compatibility": any(item["legacy_compatibility"] for item in files),
        "canonical_line": "daily",
        "files": files,
    }
    write_json(manifest, DAILY_METADATA_DIR / "daily_manifest.json")
    return manifest


def daily_downstream_contract(ready: dict | None = None) -> dict:
    ready = ready or {}
    return {
        "line": "daily",
        "provider_repo": "CNSVdata",
        "consumer_repo": "CNSV",
        "consumer_program": "CNSV_daily_main",
        "ready_path": "metadata/daily/daily_ready.json",
        "manifest_path": "metadata/daily/daily_manifest.json",
        "can_run_daily_model": bool(ready.get("ready", False)),
        "can_run_intraday_model": False,
        "can_generate_formal_signal": False,
        "created_at": now_string(),
    }


def build_daily_ready() -> dict:
    manifest = build_daily_manifest()
    required = {"cnsv_daily", "cnsv_moneyflow", "trade_calendar"}
    missing = [item["name"] for item in manifest["files"] if item["name"] in required and not item["exists"]]
    latest_trade_date, next_trade_date = _daily_trade_dates()
    status = "FAIL" if missing else "PASS"
    ready = {
        "line": "daily",
        "repo": "CNSVdata",
        "ready": not missing,
        "status": status,
        "latest_trade_date": latest_trade_date,
        "manifest_path": "metadata/daily/daily_manifest.json",
        "quality_path": "data/quality/daily/daily_quality_latest.json",
        "allowed_usage": {
            "can_run_daily_model": not missing,
            "can_run_daily_backtest": not missing,
            "can_run_intraday_model": False,
            "can_generate_formal_signal": False,
        },
        "blocking_reason": "missing_daily_core_files:" + ",".join(missing) if missing else None,
        "warnings": ["using_legacy_processed_files"] if manifest["legacy_compatibility"] else [],
        "created_at": now_string(),
    }
    write_json(ready, DAILY_METADATA_DIR / "daily_ready.json")
    write_json(daily_downstream_contract(ready), DAILY_METADATA_DIR / "daily_downstream_contract.json")
    write_json({"line": "daily", "latest_trade_date": latest_trade_date, "created_at": now_string()}, DAILY_METADATA_DIR / "daily_latest_trade_date.json")
    write_json({"line": "daily", "next_trade_date": next_trade_date, "created_at": now_string()}, DAILY_METADATA_DIR / "daily_next_trade_date.json")
    write_json(
        {
            "line": "daily",
            "status": "PASS" if not missing else "FAIL",
            "missing_core_files": missing,
            "generated_at": now_string(),
        },
        DAILY_QUALITY_DIR / "daily_gaps_latest.json",
    )
    write_json(
        {"line": "daily", "status": status, "missing": missing, "generated_at": now_string()},
        DAILY_QUALITY_DIR / "daily_quality_latest.json",
    )
    return ready


def daily_acceptance_report() -> dict:
    ready = build_daily_ready()
    checks = [
        {"name": "daily_ready_exists", "status": "PASS"},
        {"name": "daily_ready_line", "status": "PASS" if ready["line"] == "daily" else "FAIL"},
        {"name": "intraday_not_enabled_by_daily", "status": "PASS" if not ready["allowed_usage"]["can_run_intraday_model"] else "FAIL"},
        {"name": "formal_signal_disabled", "status": "PASS" if not ready["allowed_usage"]["can_generate_formal_signal"] else "FAIL"},
    ]
    status = "FAIL" if any(check["status"] == "FAIL" for check in checks) else ready["status"]
    report = {"line": "daily", "status": status, "generated_at": now_string(), "checks": checks}
    write_json(report, DAILY_QUALITY_DIR / "daily_acceptance_latest.json")
    return report


def daily_smoke_read() -> dict:
    ready_path = DAILY_METADATA_DIR / "daily_ready.json"
    status = "PASS" if ready_path.exists() else "FAIL"
    payload = {"line": "daily", "status": status, "generated_at": now_string(), "formal_signal": False}
    write_json(payload, DAILY_QUALITY_DIR / "daily_smoke_latest.json")
    return payload
