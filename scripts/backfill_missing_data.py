import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from cnsvdata.common import now_string, write_json
from cnsvdata.paths import QUALITY_DIR, ROOT

FETCH_BY_DATASET = {
    "daily": ["scripts/fetch_cnsv_daily.py"],
    "minute": ["scripts/fetch_cnsv_1min.py", "scripts/build_minute_bars.py"],
    "moneyflow": ["scripts/fetch_moneyflow.py"],
}
POST_STEPS = [
    "scripts/build_processed_daily.py",
    "scripts/build_minute_bars.py",
    "scripts/build_data_manifest.py",
    "scripts/detect_data_gaps.py",
    "scripts/quality_check.py",
    "scripts/acceptance_check.py",
    "scripts/smoke_downstream_read.py",
    "scripts/build_downstream_ready.py",
    "scripts/build_failure_summary.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill CNSVdata missing datasets without deleting existing data.")
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    parser.add_argument("--daily", action="store_true")
    parser.add_argument("--minute", action="store_true")
    parser.add_argument("--moneyflow", action="store_true")
    parser.add_argument("--from-gap-report", action="store_true")
    return parser.parse_args()


def datasets_from_gap_report() -> list[str]:
    path = QUALITY_DIR / "data_gaps_latest.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return datasets_from_gap_payload(payload)


def datasets_from_gap_payload(payload: dict) -> list[str]:
    datasets = []
    for dataset in ("daily", "minute", "moneyflow"):
        report = payload.get(dataset, {})
        if report.get("missing_trade_dates") or report.get("missing_minutes"):
            datasets.append(dataset)
    for check in payload.get("checks", []):
        if check.get("missing_count", 0) <= 0:
            continue
        name = check.get("name", "")
        if name.startswith("daily_"):
            datasets.append("daily")
        elif name.startswith("minute_"):
            datasets.append("minute")
        elif name.startswith("moneyflow_"):
            datasets.append("moneyflow")
    return sorted(set(datasets))


def selected_datasets(args: argparse.Namespace) -> list[str]:
    datasets = []
    if args.daily:
        datasets.append("daily")
    if args.minute:
        datasets.append("minute")
    if args.moneyflow:
        datasets.append("moneyflow")
    if args.from_gap_report:
        datasets.extend(datasets_from_gap_report())
    return sorted(set(datasets))


def run_step(script: str, env: dict | None = None) -> dict:
    result = subprocess.run([sys.executable, script], cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "script": script,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def main() -> None:
    args = parse_args()
    datasets = selected_datasets(args)
    env = os.environ.copy()
    if args.start_date:
        env["CNSVDATA_BACKFILL_START_DATE"] = args.start_date
    if args.end_date:
        env["CNSVDATA_BACKFILL_END_DATE"] = args.end_date
    filled = []
    failed = []
    if not datasets:
        failed.append({"dataset": "selection", "status": "FAIL", "detail": "no dataset selected"})

    for dataset in datasets:
        for script in FETCH_BY_DATASET[dataset]:
            result = run_step(script, env=env)
            item = {"dataset": dataset, "script": script, "status": result["status"]}
            if result["status"] == "PASS":
                filled.append(item)
            else:
                failed.append({**item, "detail": result})

    if not failed:
        for script in POST_STEPS:
            result = run_step(script, env=env)
            if result["status"] == "FAIL":
                failed.append({"dataset": "post_check", "script": script, "status": "FAIL", "detail": result})

    payload = {
        "status": "FAIL" if failed else "PASS",
        "generated_at": now_string(),
        "mode": "from_gap_report" if args.from_gap_report else "manual",
        "start_date": args.start_date,
        "end_date": args.end_date,
        "datasets": datasets,
        "filled": filled,
        "failed": failed,
    }
    write_json(payload, QUALITY_DIR / "backfill_latest.json")
    if payload["status"] == "FAIL":
        raise SystemExit("backfill status is FAIL")


if __name__ == "__main__":
    main()
