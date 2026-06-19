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


USAGE_LABELS = {
    "can_develop_cnsv_main_program": "Develop CNSV main program",
    "can_run_daily_ingest": "Run daily ingest",
    "can_run_backtest": "Run backtest/training",
    "can_use_moneyflow_as_strong_factor": "Use moneyflow as strong factor",
    "can_generate_formal_signal": "Generate formal signal",
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


def extract_concrete_missing_dates(gaps: dict) -> dict:
    result = {}
    for dataset in ("daily", "minute", "moneyflow"):
        report = gaps.get(dataset, {}) if isinstance(gaps.get(dataset), dict) else {}
        dates = report.get("missing_trade_dates", [])
        if dates:
            result[dataset] = dates[:30]
    return result


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


def usage_lines(allowed_usage: dict) -> list[str]:
    if not allowed_usage:
        return ["- No downstream usage decision is available."]
    lines = []
    for key, label in USAGE_LABELS.items():
        value = bool(allowed_usage.get(key, False))
        lines.append(f"- {label}: {'YES' if value else 'NO'}")
    return lines


def build_backfill_plan(gaps: dict) -> dict:
    minute = gaps.get("minute", {}) if isinstance(gaps.get("minute"), dict) else {}
    historical = gaps.get("historical_reference", {}) if isinstance(gaps.get("historical_reference"), dict) else {}
    active_missing = minute.get("missing_trade_dates", []) if isinstance(minute.get("missing_trade_dates", []), list) else []
    missing_minutes = minute.get("missing_minutes", []) if isinstance(minute.get("missing_minutes", []), list) else []
    minute_status = minute.get("status", gaps.get("status", "FAIL"))
    if minute_status == "PASS" and not active_missing:
        decision = "not_required_for_current_readiness"
        reason = "minute active coverage window is complete enough for current downstream readiness; historical gaps remain informational."
    else:
        decision = "backfill_required_before_formal_backtest"
        reason = "minute active gaps exist or current coverage is below the configured threshold."
    return {
        "sop": "docs/minute_backfill_sop.md",
        "dataset": "minute",
        "decision": decision,
        "reason": reason,
        "coverage_scope": minute.get("coverage_scope", ""),
        "active_missing_trade_dates": active_missing,
        "active_missing_count": len(active_missing),
        "tolerated_missing_minutes": missing_minutes if minute_status == "PASS" else [],
        "historical_missing_count": int(historical.get("minute_missing_count", 0) or 0),
        "command_when_required": "python scripts/backfill_missing_data.py --minute",
        "post_check": "pytest && python scripts/detect_data_gaps.py && python scripts/quality_check.py && python scripts/acceptance_check.py",
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# CNSVdata Failure Summary",
        "",
        "## Overall Status",
        "",
        payload["status"],
        "",
        f"- Failed count: {payload.get('failed_count', 0)}",
        f"- Warning count: {payload.get('warn_count', 0)}",
        "",
        "## Blocking",
        "",
        str(payload["blocking"]).lower(),
        "",
        f"- Blocking reason: {payload.get('blocking_reason') or 'None'}",
        "",
        "## Can CNSV Main Start?",
        "",
        "YES" if payload.get("can_cnsv_main_start") else "NO",
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
    lines.extend(["## Concrete Missing Dates", ""])
    if not payload.get("concrete_missing_dates"):
        lines.append("None")
    for dataset, dates in payload.get("concrete_missing_dates", {}).items():
        lines.append(f"- {dataset}: {', '.join(dates)}")
    lines.extend(["", "## Suggested Backfill Commands", ""])
    if not payload.get("suggested_backfill_commands"):
        lines.append("None")
    for command in payload.get("suggested_backfill_commands", []):
        lines.append(f"- `{command}`")
    plan = payload.get("backfill_plan", {})
    lines.extend(["", "## Minute Backfill Plan", ""])
    if not plan:
        lines.append("None")
    else:
        lines.extend(
            [
                f"- SOP: `{plan.get('sop', '')}`",
                f"- Decision: {plan.get('decision', '')}",
                f"- Reason: {plan.get('reason', '')}",
                f"- Coverage scope: {plan.get('coverage_scope', '')}",
                f"- Active missing trade dates: {plan.get('active_missing_count', 0)}",
                f"- Historical missing count: {plan.get('historical_missing_count', 0)}",
                f"- Command when required: `{plan.get('command_when_required', '')}`",
            ]
        )
    lines.extend(["", "## Allowed Usage", ""])
    lines.extend(usage_lines(payload.get("allowed_usage", {})))
    lines.extend(["", "## Next Action", "", payload.get("next_action", "Inspect the source report and rerun affected checks.")])
    return "\n".join(lines).rstrip() + "\n"


def build_summary() -> dict:
    failures, warnings, source_statuses = collect_items()
    status = aggregate_status(source_statuses + failures + warnings)
    downstream = read_json(ROOT / "metadata" / "downstream_ready.json")
    gaps = read_json(QUALITY_DIR / "data_gaps_latest.json")
    allowed_usage = downstream.get("allowed_usage", {})
    blocking = status == "FAIL"
    backfill_plan = build_backfill_plan(gaps)
    next_action = "start CNSV main program connection development with formal-signal gate disabled and minute backfill SOP documented"
    if blocking:
        next_action = failures[0]["suggested_action"] if failures else "rerun the acceptance workflow from the beginning"
    elif warnings:
        next_action = "review WARN impacts, run suggested backfills when source data becomes available, then rerun acceptance"
    return {
        "status": status,
        "generated_at": now_string(),
        "blocking": blocking,
        "blocking_reason": downstream.get("blocking_reason"),
        "can_cnsv_main_start": bool(allowed_usage.get("can_develop_cnsv_main_program", False)) and not blocking,
        "failed_count": len(failures),
        "warn_count": len(warnings),
        "top_failures": failures[:20],
        "top_warnings": warnings[:20],
        "concrete_missing_dates": extract_concrete_missing_dates(gaps),
        "suggested_backfill_commands": gaps.get("suggested_backfill_commands", []) if isinstance(gaps.get("suggested_backfill_commands", []), list) else [],
        "backfill_plan": backfill_plan,
        "allowed_usage": allowed_usage,
        "next_action": next_action,
    }


def main() -> None:
    payload = build_summary()
    write_json(payload, QUALITY_DIR / "failure_summary_latest.json")
    (QUALITY_DIR / "failure_summary_latest.md").write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
