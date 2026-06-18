from pathlib import Path

import pandas as pd

from cnsvdata.paths import PROCESSED_DIR, ROOT

PREVIEW_DIR = ROOT / "data" / "preview"

PREVIEW_FILES = {
    "trade_calendar": {
        "source": PROCESSED_DIR / "trade_calendar.parquet",
        "target": PREVIEW_DIR / "trade_calendar_latest.csv",
        "tail_rows": 260,
        "sort_column": "cal_date",
    },
    "cnsv_daily": {
        "source": PROCESSED_DIR / "cnsv_daily.parquet",
        "target": PREVIEW_DIR / "cnsv_daily_latest.csv",
        "tail_rows": 260,
        "sort_column": "trade_date",
    },
    "cnsv_moneyflow": {
        "source": PROCESSED_DIR / "cnsv_moneyflow.parquet",
        "target": PREVIEW_DIR / "cnsv_moneyflow_latest.csv",
        "tail_rows": 260,
        "sort_column": "trade_date",
    },
    "cnsv_1min": {
        "source": PROCESSED_DIR / "cnsv_1min.parquet",
        "target": PREVIEW_DIR / "cnsv_1min_latest.csv",
        "tail_rows": 500,
        "sort_column": "trade_time",
    },
    "cnsv_5min": {
        "source": PROCESSED_DIR / "cnsv_5min.parquet",
        "target": PREVIEW_DIR / "cnsv_5min_latest.csv",
        "tail_rows": 500,
        "sort_column": "trade_time",
    },
    "cnsv_15min": {
        "source": PROCESSED_DIR / "cnsv_15min.parquet",
        "target": PREVIEW_DIR / "cnsv_15min_latest.csv",
        "tail_rows": 500,
        "sort_column": "trade_time",
    },
    "cnsv_30min": {
        "source": PROCESSED_DIR / "cnsv_30min.parquet",
        "target": PREVIEW_DIR / "cnsv_30min_latest.csv",
        "tail_rows": 500,
        "sort_column": "trade_time",
    },
    "cnsv_60min": {
        "source": PROCESSED_DIR / "cnsv_60min.parquet",
        "target": PREVIEW_DIR / "cnsv_60min_latest.csv",
        "tail_rows": 500,
        "sort_column": "trade_time",
    },
    "corporate_actions": {
        "source": PROCESSED_DIR / "corporate_actions.parquet",
        "target": PREVIEW_DIR / "corporate_actions.csv",
        "tail_rows": None,
        "sort_column": "event_date",
    },
    "structural_breaks": {
        "source": PROCESSED_DIR / "structural_breaks.parquet",
        "target": PREVIEW_DIR / "structural_breaks.csv",
        "tail_rows": None,
        "sort_column": "start_date",
    },
}


def write_preview(source: Path, target: Path, sort_column: str, tail_rows: int | None) -> dict:
    if not source.exists():
        return {"path": str(source.relative_to(ROOT)), "status": "missing"}

    df = pd.read_parquet(source)
    if sort_column in df.columns:
        df = df.sort_values(sort_column)
    if tail_rows:
        df = df.tail(tail_rows)

    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False, encoding="utf-8-sig")
    return {
        "path": str(target.relative_to(ROOT)),
        "status": "written",
        "rows": int(len(df)),
        "source": str(source.relative_to(ROOT)),
    }


def main() -> None:
    results = []
    for spec in PREVIEW_FILES.values():
        results.append(write_preview(**spec))

    summary = pd.DataFrame(results)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(PREVIEW_DIR / "preview_manifest.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
