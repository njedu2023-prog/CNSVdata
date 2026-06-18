import shutil

from cnsvdata.common import now_string
from cnsvdata.paths import METADATA_DIR, QUALITY_DIR

QUALITY_FILES = [
    "data_quality_latest.json",
    "acceptance_latest.json",
    "downstream_smoke_latest.json",
    "data_gaps_latest.json",
    "failure_summary_latest.json",
    "failure_summary_latest.md",
]
METADATA_FILES = ["data_manifest.json", "data_snapshot.json", "downstream_ready.json"]


def copy_if_exists(source, target_dir) -> bool:
    if not source.exists():
        return False
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target_dir / source.name)
    return True


def archive_snapshot() -> dict:
    date_dir = now_string()[:10]
    quality_target = QUALITY_DIR / "history" / date_dir
    metadata_target = METADATA_DIR / "history" / date_dir
    copied = []
    missing = []
    for name in QUALITY_FILES:
        if copy_if_exists(QUALITY_DIR / name, quality_target):
            copied.append(f"data/quality/{name}")
        else:
            missing.append(f"data/quality/{name}")
    for name in METADATA_FILES:
        if copy_if_exists(METADATA_DIR / name, metadata_target):
            copied.append(f"metadata/{name}")
        else:
            missing.append(f"metadata/{name}")
    return {"date": date_dir, "copied": copied, "missing": missing}


def main() -> None:
    archive_snapshot()


if __name__ == "__main__":
    main()
