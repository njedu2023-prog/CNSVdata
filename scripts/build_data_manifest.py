import hashlib
import json
from pathlib import Path

import pandas as pd

from cnsvdata.common import file_sha256, load_yaml, normalize_trade_date, now_string, write_json
from cnsvdata.paths import METADATA_DIR, ROOT


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def persisted_latest_trade_date() -> str:
    return normalize_trade_date(read_json(METADATA_DIR / "latest_trade_date.json").get("latest_trade_date", ""))


def persisted_next_trade_date() -> str:
    return normalize_trade_date(read_json(METADATA_DIR / "next_trade_date.json").get("next_trade_date", ""))


def quality_status() -> str:
    return read_json(ROOT / "data" / "quality" / "data_quality_latest.json").get("status", "UNKNOWN")


def ready_status() -> str:
    payload = read_json(METADATA_DIR / "downstream_ready.json")
    return payload.get("status", "UNKNOWN")


def date_range_for_df(df: pd.DataFrame) -> tuple[str | None, str | None]:
    for column in ("trade_date", "cal_date", "event_date", "start_date"):
        if column in df.columns and not df[column].dropna().empty:
            values = df[column].dropna().astype(str).map(normalize_trade_date)
            return str(values.min()), str(values.max())
    return None, None


def manifest_item(relative_path: str, generated_at: str) -> dict:
    path = ROOT / relative_path
    item = {
        "path": relative_path,
        "exists": path.exists(),
        "rows": 0,
        "columns": [],
        "sha256": "",
        "file_size": 0,
        "min_trade_date": None,
        "max_trade_date": None,
        "updated_at": generated_at,
        "source": "tushare",
        "status": "FAIL",
    }
    if not path.exists():
        return item

    item["file_size"] = int(path.stat().st_size)
    item["sha256"] = file_sha256(path)
    if path.suffix == ".parquet":
        try:
            df = pd.read_parquet(path)
            item["rows"] = int(len(df))
            item["columns"] = list(df.columns)
            item["min_trade_date"], item["max_trade_date"] = date_range_for_df(df)
            item["status"] = "PASS" if len(df) > 0 and len(df.columns) > 0 else "WARN"
        except Exception as exc:
            item["status"] = "FAIL"
            item["error"] = str(exc)
    elif path.suffix == ".json":
        try:
            payload = read_json(path)
            item["rows"] = 1 if payload else 0
            item["columns"] = list(payload.keys()) if isinstance(payload, dict) else []
            item["status"] = "PASS" if payload else "WARN"
        except Exception as exc:
            item["status"] = "FAIL"
            item["error"] = str(exc)
    else:
        item["status"] = "PASS" if item["file_size"] > 0 else "WARN"
    return item


def derived_latest_trade_date(files: list[dict]) -> str:
    core_paths = {
        "data/processed/cnsv_daily.parquet",
        "data/processed/cnsv_1min.parquet",
        "data/processed/cnsv_moneyflow.parquet",
    }
    dates = [item.get("max_trade_date") for item in files if item.get("path") in core_paths and item.get("max_trade_date")]
    if dates:
        return max(normalize_trade_date(date) for date in dates)
    return persisted_latest_trade_date()


def derived_next_trade_date(latest: str) -> str:
    calendar_path = ROOT / "data" / "processed" / "trade_calendar.parquet"
    if calendar_path.exists() and latest:
        try:
            calendar = pd.read_parquet(calendar_path)
            if "cal_date" in calendar.columns:
                dates = calendar["cal_date"].dropna().astype(str).map(normalize_trade_date)
                if "is_open" in calendar.columns:
                    dates = dates[calendar["is_open"].astype(int) == 1]
                future = sorted(date for date in dates if date > latest)
                if future:
                    return future[0]
        except Exception:
            pass
    return persisted_next_trade_date()


def write_trade_date_metadata(latest: str, next_date: str, generated_at: str) -> None:
    write_json(
        {
            "latest_trade_date": latest,
            "source": "processed_core_parquet",
            "generated_at": generated_at,
            "timezone": "Asia/Shanghai",
        },
        METADATA_DIR / "latest_trade_date.json",
    )
    write_json(
        {
            "next_trade_date": next_date,
            "source": "trade_calendar_after_latest_trade_date",
            "latest_trade_date": latest,
            "generated_at": generated_at,
            "timezone": "Asia/Shanghai",
        },
        METADATA_DIR / "next_trade_date.json",
    )


def build_manifest(required_files: list[str]) -> dict:
    generated_at = now_string()
    field_contract = load_yaml("field_contract.yml")["contract"]
    files = [manifest_item(relative, generated_at) for relative in required_files]
    latest = derived_latest_trade_date(files)
    next_date = derived_next_trade_date(latest)
    write_trade_date_metadata(latest, next_date, generated_at)
    snapshot_seed = json.dumps(files, sort_keys=True, ensure_ascii=False).encode("utf-8")
    snapshot_hash = hashlib.sha256(snapshot_seed).hexdigest()
    snapshot_id = f"cnsvdata-{latest or generated_at[:10]}-{snapshot_hash[:12]}"
    return {
        "snapshot_id": snapshot_id,
        "generated_at": generated_at,
        "latest_trade_date": latest,
        "next_trade_date": next_date,
        "contract_version": field_contract.get("version", ""),
        "quality_status": quality_status(),
        "ready_status": ready_status(),
        "source": "tushare",
        "files": files,
    }


def main() -> None:
    contract = load_yaml("data_contract.yml")["contract"]
    manifest = build_manifest(contract["required_files"])
    snapshot_hash = hashlib.sha256(json.dumps(manifest["files"], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    write_json(manifest, METADATA_DIR / "data_manifest.json")
    write_json(
        {
            "data_snapshot_id": manifest["snapshot_id"],
            "data_snapshot_hash": snapshot_hash,
            "generated_at": manifest["generated_at"],
            "latest_trade_date": manifest["latest_trade_date"],
            "next_trade_date": manifest["next_trade_date"],
            "contract_version": manifest["contract_version"],
            "quality_status": manifest["quality_status"],
            "ready_status": manifest["ready_status"],
            "files": manifest["files"],
        },
        METADATA_DIR / "data_snapshot.json",
    )


if __name__ == "__main__":
    main()
