import json
from pathlib import Path

from cnsvdata.common import now_string, write_json
from cnsvdata.paths import QUALITY_DIR, ROOT
from cnsvdata.validators import aggregate_status

SOURCES = {
    "quality": QUALITY_DIR / "data_quality_latest.json",
    "acceptance": QUALITY_DIR / "acceptance_latest.json",
    "smoke": QUALITY_DIR / "downstream_smoke_latest.json",
    "gaps": QUALITY_DIR / "data_gaps_latest.json",
}


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def suggested_action(name: str, detail: str = "") -> str:
    text = f"{name} {detail}".lower()
    if "minute" in text:
        return "rerun fetch_minute, build_minute_bars, quality, acceptance, and smoke checks"
    if "moneyflow" in text:
        return "rerun fetch_moneyflow, build manifest, quality, acceptance, and smoke checks"
    if "daily" in text:
        return "rerun fetch_cnsv_daily, build processed data, quality, acceptance, and smoke checks"
    if "manifest" in text:
        return "rerun build_data_manifest after source data and quality reports are updated"
    if "missing" in text:
        return "run detect_data_gaps and backfill_missing_data for the affected dataset"
    return "inspect the source report and rerun the affected data pipeline step"


def collect_items() -> tuple[list[dict], list[dict], list[dict]]:
    failures = []
    warnings = []
    source_statuses = []
    for source, path in SOURCES.items():
        payload = read_json(path)
        if not payload:
            failures.append(
                {
                    "source": source,
                    "name": f"missing_report:{path.relative_to(ROOT)}",
                    "status": "FAIL",
                    "detail": "report file is missing",
                    "suggested_action": "rerun the acceptance workflow from the beginning",
                }
            )
            source_statuses.append({"status": "FAIL"})
            continue
        source_statuses.append({"status": payload.get("status", "FAIL")})
        for check in payload.get("checks", []):
            status = check.get("status")
            if status not in {"FAIL", "WARN"}:
                continue
            item = {
                "source": source,
                "name": check.get("name", "unnamed_check"),
                "status": status,
                "detail": check.get("detail", ""),
                "suggested_action": suggested_action(check.get("name", ""), check.get("detail", "")),
            }
            if status == "FAIL":
                failures.append(item)
            else:
                warnings.append(item)
    return failures, warnings, source_statuses


def render_markdown(payload: dict) -> str:
    lines = [
        "# CNSVdata Failure Summary",
        "",
        "## Overall Status",
        "",
        payload["status"],
        "",
        "## Blocking",
        "",
        str(payload["blocking"]).lower(),
        "",
        "## Top Failures",
        "",
    ]
    if not payload["top_failures"]:
        lines.append("None")
    for index, item in enumerate(payload["top_failures"], 1):
        lines.extend(
            [
                f"### {index}. {item['name']}",
                "",
                f"- Source: {item['source']}",
                f"- Status: {item['status']}",
                f"- Detail: {item.get('detail', '')}",
                f"- Suggested action: {item['suggested_action']}",
                "",
            ]
        )
    lines.extend(["## Top Warnings", ""])
    if not payload["top_warnings"]:
        lines.append("None")
    for index, item in enumerate(payload["top_warnings"], 1):
        lines.extend(
            [
                f"### {index}. {item['name']}",
                "",
                f"- Source: {item['source']}",
                f"- Status: {item['status']}",
                f"- Detail: {item.get('detail', '')}",
                f"- Suggested action: {item['suggested_action']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_summary() -> dict:
    failures, warnings, source_statuses = collect_items()
    status = aggregate_status(source_statuses + failures + warnings)
    return {
        "status": status,
        "generated_at": now_string(),
        "blocking": status == "FAIL",
        "failed_count": len(failures),
        "warn_count": len(warnings),
        "top_failures": failures[:20],
        "top_warnings": warnings[:20],
    }


def main() -> None:
    payload = build_summary()
    write_json(payload, QUALITY_DIR / "failure_summary_latest.json")
    (QUALITY_DIR / "failure_summary_latest.md").write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
