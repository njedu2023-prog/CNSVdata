import hashlib
import json
from pathlib import Path

import pandas as pd

from cnsvdata.common import file_sha256, now_string, write_json
from cnsvdata.paths import METADATA_DIR, PROCESSED_DIR, ROOT


def latest_trade_date() -> str:
    path = METADATA_DIR / "latest_trade_date.json"
    if not path.exists():
        return ""
    return json.loads(path.read_text(encoding="utf-8")).get("latest_trade_date", "")


def main() -> None:
    generated_at = now_string()
    latest = latest_trade_date()
    files = []
    for path in sorted(PROCESSED_DIR.glob("*.parquet")):
        df = pd.read_parquet(path)
        files.append(
            {
                "path": str(path.relative_to(ROOT)),
                "rows": int(len(df)),
                "columns": list(df.columns),
                "sha256": file_sha256(path),
                "updated_at": generated_at,
            }
        )
    snapshot_seed = json.dumps(files, sort_keys=True, ensure_ascii=False).encode("utf-8")
    snapshot_hash = hashlib.sha256(snapshot_seed).hexdigest()
    snapshot_id = f"cnsvdata-{latest or generated_at[:10]}-{snapshot_hash[:12]}"
    manifest = {
        "snapshot_id": snapshot_id,
        "generated_at": generated_at,
        "latest_trade_date": latest,
        "source": "tushare",
        "files": files,
    }
    write_json(manifest, METADATA_DIR / "data_manifest.json")
    write_json(
        {
            "data_snapshot_id": snapshot_id,
            "data_snapshot_hash": snapshot_hash,
            "generated_at": generated_at,
            "latest_trade_date": latest,
            "files": files,
        },
        METADATA_DIR / "data_snapshot.json",
    )


if __name__ == "__main__":
    main()
