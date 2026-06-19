import json
from pathlib import Path

from cnsvdata.common import load_yaml, now_string, write_json
from cnsvdata.paths import METADATA_DIR, QUALITY_DIR
from cnsvdata.validators import aggregate_status


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def status_of(path: Path) -> str:
    return read_json(path).get("status", "FAIL")


def warn_checks_from_report(source: str, report: dict) -> list[dict]:
    warnings = []
    for check in report.get("checks", []):
        if check.get("status") != "WARN":
            continue
        warnings.append(
            {
                "source": source,
                "name": check.get("name", "unnamed_check"),
                "detail": check.get("detail", ""),
                "missing_count": int(check.get("missing_count", 0) or 0),
            }
        )
    return warnings


def report_failure_reason(report: dict) -> str | None:
    failed = [check for check in report.get("checks", []) if check.get("status") == "FAIL"]
    failed_names = {check.get("name", "") for check in failed}
    minute_names = {
        "required_file:data/processed/cnsv_1min.parquet",
        "required_file:data/processed/cnsv_5min.parquet",
        "required_file:data/processed/cnsv_15min.parquet",
        "required_file:data/processed/cnsv_30min.parquet",
        "required_file:data/processed/cnsv_60min.parquet",
        "cnsv_1min.parquet_exists",
        "parquet_readable:cnsv_1min.parquet",
    }
    if failed_names & minute_names:
        return "core minute parquet missing"
    if failed:
        first = failed[0]
        return f"{first.get('name', 'unknown_check')} failed"
    return None


def first_blocking_reason(statuses: dict[str, str]) -> str | None:
    for name, status in statuses.items():
        if status == "FAIL":
            return f"{name} failed"
    return None


def detailed_blocking_reason(statuses: dict[str, str]) -> str | None:
    for name, filename in (
        ("quality_check", "data_quality_latest.json"),
        ("data_gaps_check", "data_gaps_latest.json"),
        ("acceptance_check", "acceptance_latest.json"),
        ("smoke_check", "downstream_smoke_latest.json"),
    ):
        if statuses.get(name) == "FAIL":
            reason = report_failure_reason(read_json(QUALITY_DIR / filename))
            return reason or f"{name} failed"
    return None


def allowed_usage(status: str, warnings: list[dict]) -> dict:
    if status == "FAIL":
        return {
            "can_develop_cnsv_main_program": False,
            "can_run_daily_ingest": False,
            "can_run_backtest": False,
            "can_use_moneyflow_as_strong_factor": False,
            "can_generate_formal_signal": False,
        }
    moneyflow_warn = any("moneyflow" in item.get("name", "").lower() or "moneyflow" in item.get("source", "").lower() for item in warnings)
    return {
        "can_develop_cnsv_main_program": True,
        "can_run_daily_ingest": True,
        "can_run_backtest": status == "PASS",
        "can_use_moneyflow_as_strong_factor": status == "PASS" and not moneyflow_warn,
        "can_generate_formal_signal": False,
    }


def build_ready() -> dict:
    manifest = read_json(METADATA_DIR / "data_manifest.json")
    contract = load_yaml("field_contract.yml")["contract"]
    quality = read_json(QUALITY_DIR / "data_quality_latest.json")
    gaps = read_json(QUALITY_DIR / "data_gaps_latest.json")
    acceptance = read_json(QUALITY_DIR / "acceptance_latest.json")
    smoke = read_json(QUALITY_DIR / "downstream_smoke_latest.json")
    statuses = {
        "quality_check": quality.get("status", "FAIL"),
        "data_gaps_check": gaps.get("status", "FAIL"),
        "acceptance_check": acceptance.get("status", "FAIL"),
        "smoke_check": smoke.get("status", "FAIL"),
    }
    status = aggregate_status([{"status": value} for value in statuses.values()])
    warnings = (
        warn_checks_from_report("quality", quality)
        + warn_checks_from_report("data_gaps", gaps)
        + warn_checks_from_report("acceptance", acceptance)
        + warn_checks_from_report("smoke", smoke)
    )[:50]
    return {
        "ready": status in {"PASS", "WARN"},
        "status": status,
        "generated_at": now_string(),
        "latest_trade_date": manifest.get("latest_trade_date", ""),
        "quality_status": statuses["quality_check"],
        "data_gaps_status": statuses["data_gaps_check"],
        "acceptance_status": statuses["acceptance_check"],
        "smoke_status": statuses["smoke_check"],
        "contract_version": contract.get("version", ""),
        "manifest_snapshot_id": manifest.get("snapshot_id", ""),
        "blocking_reason": detailed_blocking_reason(statuses),
        "warnings": warnings,
        "allowed_usage": allowed_usage(status, warnings),
    }


def main() -> None:
    write_json(build_ready(), METADATA_DIR / "downstream_ready.json")


if __name__ == "__main__":
    main()
