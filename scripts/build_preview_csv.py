from pathlib import Path

import pandas as pd

from cnsvdata.common import now_string
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
    generated_at = now_string()
    source_file = str(source.relative_to(ROOT))
    preview_file = str(target.relative_to(ROOT))
    if not source.exists():
        return {
            "preview_file": preview_file,
            "source_file": source_file,
            "rows": 0,
            "columns": "",
            "min_date": "",
            "max_date": "",
            "generated_at": generated_at,
            "status": "missing_source",
        }

    df = pd.read_parquet(source)
    min_date = ""
    max_date = ""
    for column in (sort_column, "trade_date", "cal_date", "event_date", "start_date"):
        if column in df.columns and not df[column].dropna().empty:
            values = df[column].dropna().astype(str)
            min_date = values.min()
            max_date = values.max()
            break
    if sort_column in df.columns:
        df = df.sort_values(sort_column)
    if tail_rows:
        df = df.tail(tail_rows)

    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False, encoding="utf-8-sig")
    return {
        "preview_file": preview_file,
        "source_file": source_file,
        "rows": int(len(df)),
        "columns": ",".join(df.columns.astype(str).tolist()),
        "min_date": min_date,
        "max_date": max_date,
        "generated_at": generated_at,
        "status": "empty" if df.empty else "written",
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
