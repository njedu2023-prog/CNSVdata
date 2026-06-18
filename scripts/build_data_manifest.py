import hashlib
import json
from pathlib import Path

import pandas as pd

from cnsvdata.common import file_sha256, load_yaml, now_string, write_json
from cnsvdata.paths import METADATA_DIR, ROOT


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def latest_trade_date() -> str:
    return read_json(METADATA_DIR / "latest_trade_date.json").get("latest_trade_date", "")


def next_trade_date() -> str:
    return read_json(METADATA_DIR / "next_trade_date.json").get("next_trade_date", "")


def quality_status() -> str:
    return read_json(ROOT / "data" / "quality" / "data_quality_latest.json").get("status", "UNKNOWN")


def date_range_for_df(df: pd.DataFrame) -> tuple[str | None, str | None]:
    for column in ("trade_date", "cal_date", "event_date", "start_date"):
        if column in df.columns and not df[column].dropna().empty:
            values = df[column].dropna().astype(str)
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


def build_manifest(required_files: list[str]) -> dict:
    generated_at = now_string()
    latest = latest_trade_date()
    files = [manifest_item(relative, generated_at) for relative in required_files]
    snapshot_seed = json.dumps(files, sort_keys=True, ensure_ascii=False).encode("utf-8")
    snapshot_hash = hashlib.sha256(snapshot_seed).hexdigest()
    snapshot_id = f"cnsvdata-{latest or generated_at[:10]}-{snapshot_hash[:12]}"
    return {
        "snapshot_id": snapshot_id,
        "generated_at": generated_at,
        "latest_trade_date": latest,
        "next_trade_date": next_trade_date(),
        "quality_status": quality_status(),
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
            "quality_status": manifest["quality_status"],
            "files": manifest["files"],
        },
        METADATA_DIR / "data_snapshot.json",
    )


if __name__ == "__main__":
    main()
