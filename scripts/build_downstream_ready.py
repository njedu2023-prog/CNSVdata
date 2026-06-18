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


def first_blocking_reason(statuses: dict[str, str]) -> str | None:
    for name, status in statuses.items():
        if status == "FAIL":
            return f"{name} failed"
    return None


def build_ready() -> dict:
    manifest = read_json(METADATA_DIR / "data_manifest.json")
    contract = load_yaml("field_contract.yml")["contract"]
    statuses = {
        "quality_check": status_of(QUALITY_DIR / "data_quality_latest.json"),
        "acceptance_check": status_of(QUALITY_DIR / "acceptance_latest.json"),
        "smoke_check": status_of(QUALITY_DIR / "downstream_smoke_latest.json"),
    }
    status = aggregate_status([{"status": value} for value in statuses.values()])
    return {
        "ready": status in {"PASS", "WARN"},
        "status": status,
        "generated_at": now_string(),
        "latest_trade_date": manifest.get("latest_trade_date", ""),
        "quality_status": statuses["quality_check"],
        "acceptance_status": statuses["acceptance_check"],
        "smoke_status": statuses["smoke_check"],
        "contract_version": contract.get("version", ""),
        "manifest_snapshot_id": manifest.get("snapshot_id", ""),
        "blocking_reason": first_blocking_reason(statuses),
    }


def main() -> None:
    write_json(build_ready(), METADATA_DIR / "downstream_ready.json")


if __name__ == "__main__":
    main()
