from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd

from cnsvdata.common import load_yaml, now_string, write_json, write_parquet
from cnsvdata.intraday import (
    ASOF_TIME,
    DEFAULT_HISTORY_DAYS,
    INSUFFICIENT_HISTORY_REASON,
    INTRADAY_QUALITY_DIR,
    INTRADAY_RAW_PATH,
    MINUTE_COLUMNS,
    compact_trade_date,
    normalize_intraday_minutes,
)
from cnsvdata.paths import DATA_DIR, METADATA_DIR
from cnsvdata.tushare_client import call_with_retry, get_tushare_pro

BACKFILL_REPORT_PATH = INTRADAY_QUALITY_DIR / "intraday_backfill_latest.json"
SOURCE_PERMISSION_INSUFFICIENT = "source_permission_insufficient"


def _target() -> dict:
    return load_yaml("target.yml").get("target", {})


def _compact_or_empty(value: str | None) -> str:
    if not value:
        return ""
    return compact_trade_date(value)


def _latest_trade_date() -> str:
    path = METADATA_DIR / "daily" / "daily_latest_trade_date.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        latest = _compact_or_empty(payload.get("latest_trade_date"))
        if latest:
            return latest
    daily_path = DATA_DIR / "daily" / "processed" / "cnsv_daily.parquet"
    if daily_path.exists():
        daily = pd.read_parquet(daily_path)
        if "trade_date" in daily.columns and not daily.empty:
            return sorted(daily["trade_date"].dropna().astype(str).map(compact_trade_date).unique())[-1]
    return ""


def calendar_path() -> Path:
    candidates = [
        DATA_DIR / "daily" / "processed" / "trade_calendar.parquet",
        DATA_DIR / "processed" / "trade_calendar.parquet",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def trade_window(history_days: int, end_date: str = "") -> list[str]:
    path = calendar_path()
    if not path.exists():
        return []
    calendar = pd.read_parquet(path)
    column = "cal_date" if "cal_date" in calendar.columns else "trade_date"
    if column not in calendar.columns:
        return []
    if "is_open" in calendar.columns:
        calendar = calendar[pd.to_numeric(calendar["is_open"], errors="coerce") == 1]
    end = _compact_or_empty(end_date) or _latest_trade_date()
    dates = sorted(calendar[column].dropna().astype(str).map(compact_trade_date).unique())
    if end:
        dates = [date for date in dates if date <= end]
    return dates[-history_days:]


def _permission_error(exc: Exception) -> bool:
    text = str(exc).lower()
    markers = [
        "permission", "权限", "无权限", "没有权限", "抱歉", "积分", "access denied",
        "not authorized", "not have", "token",
    ]
    return any(marker in text for marker in markers)


def _empty_minutes(ts_code: str, trade_date: str) -> pd.DataFrame:
    return pd.DataFrame(columns=MINUTE_COLUMNS).assign(ts_code=ts_code, trade_date=trade_date)


def _dashed_trade_date(trade_date: str) -> str:
    compact = compact_trade_date(trade_date)
    return f"{compact[:4]}-{compact[4:6]}-{compact[6:]}"


def _minute_date_ranges(trade_date: str) -> list[tuple[str, str]]:
    dashed = _dashed_trade_date(trade_date)
    compact = compact_trade_date(trade_date)
    return [
        (f"{dashed} 09:30:00", f"{dashed} 14:00:00"),
        (f"{compact} 09:30:00", f"{compact} 14:00:00"),
        (compact, compact),
    ]


def fetch_one_day(pro, ts_code: str, trade_date: str, retry_times: int, retry_sleep_seconds: int) -> pd.DataFrame:
    import tushare as ts

    freq = load_yaml("tushare.yml").get("tushare", {}).get("minute_freq", "1min")
    last_error: Exception | None = None
    for start_date, end_date in _minute_date_ranges(trade_date):
        params = {"ts_code": ts_code, "freq": freq, "start_date": start_date, "end_date": end_date}
        strategies = [
            ("tushare_stk_mins", pro.stk_mins, params),
            ("tushare_pro_bar", ts.pro_bar, {**params, "api": pro, "asset": "E", "retry_count": retry_times}),
        ]
        for source, fn, kwargs in strategies:
            try:
                raw = call_with_retry(fn, retry_times=retry_times, sleep_seconds=retry_sleep_seconds, **kwargs)
            except Exception as exc:
                if _permission_error(exc):
                    raise
                last_error = exc
                continue
            if raw is None or raw.empty:
                continue
            normalized = normalize_intraday_minutes(raw, source=source)
            normalized = normalized[normalized["trade_date"].astype(str) == compact_trade_date(trade_date)].copy()
            if not normalized.empty:
                return normalized
    if last_error is not None:
        raise last_error
    return _empty_minutes(ts_code, trade_date)


def existing_intraday_raw() -> pd.DataFrame:
    if not INTRADAY_RAW_PATH.exists():
        return pd.DataFrame(columns=MINUTE_COLUMNS)
    return normalize_intraday_minutes(pd.read_parquet(INTRADAY_RAW_PATH), source=INTRADAY_RAW_PATH.name)


def write_backfill_report(
    *,
    status: str,
    reason: str | None,
    required_trade_days: int,
    target_trade_days: list[str],
    actual_trade_days: int,
    fetched_trade_days: list[str],
    failed_trade_days: list[dict],
    ts_code: str,
    output_path: Path = INTRADAY_RAW_PATH,
) -> dict:
    payload = {
        "line": "intraday_1400",
        "status": status,
        "reason": reason,
        "required_trade_days": int(required_trade_days),
        "target_trade_days": target_trade_days,
        "actual_trade_days": int(actual_trade_days),
        "fetched_trade_days": fetched_trade_days,
        "failed_trade_days": failed_trade_days,
        "can_train_model": bool(actual_trade_days >= required_trade_days and status == "PASS"),
        "ts_code": ts_code,
        "output_path": str(output_path),
        "source": "tushare.stk_mins",
        "asof_time": ASOF_TIME,
        "created_at": now_string(),
    }
    write_json(payload, BACKFILL_REPORT_PATH)
    return payload


def backfill_intraday_1min_history(history_days: int, end_date: str = "", ts_code: str = "") -> dict:
    target = _target()
    code = ts_code or target.get("ts_code", "600150.SH")
    dates = trade_window(history_days, end_date)
    cfg = load_yaml("tushare.yml").get("tushare", {})
    retry_times = int(cfg.get("retry_times", 3))
    retry_sleep_seconds = int(cfg.get("retry_sleep_seconds", 5))
    existing = existing_intraday_raw()
    frames = [existing] if not existing.empty else []
    fetched: list[str] = []
    failed: list[dict] = []
    permission_blocked = False

    try:
        pro = get_tushare_pro()
    except Exception as exc:
        return write_backfill_report(
            status="FAIL",
            reason=SOURCE_PERMISSION_INSUFFICIENT,
            required_trade_days=history_days,
            target_trade_days=dates,
            actual_trade_days=int(existing["trade_date"].nunique()) if not existing.empty else 0,
            fetched_trade_days=fetched,
            failed_trade_days=[{"trade_date": "", "reason": SOURCE_PERMISSION_INSUFFICIENT, "detail": str(exc)}],
            ts_code=code,
        )

    for trade_date in dates:
        try:
            day = fetch_one_day(pro, code, trade_date, retry_times, retry_sleep_seconds)
        except Exception as exc:
            reason = SOURCE_PERMISSION_INSUFFICIENT if _permission_error(exc) else "source_fetch_failed"
            failed.append({"trade_date": trade_date, "reason": reason, "detail": str(exc)})
            if reason == SOURCE_PERMISSION_INSUFFICIENT:
                permission_blocked = True
                break
            continue
        if day.empty:
            failed.append({"trade_date": trade_date, "reason": "empty_source_response"})
            continue
        frames.append(day)
        fetched.append(trade_date)

    merged = normalize_intraday_minutes(pd.concat(frames, ignore_index=True), "intraday_backfill") if frames else pd.DataFrame(columns=MINUTE_COLUMNS)
    if not merged.empty:
        merged = merged[merged["trade_date"].astype(str).isin(dates)].copy()
        merged = merged.drop_duplicates(subset=["trade_date", "trade_time", "ts_code"], keep="last")
        merged = merged.sort_values(["trade_date", "trade_time", "ts_code"]).reset_index(drop=True)
        write_parquet(merged, INTRADAY_RAW_PATH)

    actual = int(merged["trade_date"].nunique()) if not merged.empty else 0
    if permission_blocked:
        status = "FAIL"
        reason = SOURCE_PERMISSION_INSUFFICIENT
    elif actual >= history_days:
        status = "PASS"
        reason = None
    else:
        status = "WARN"
        reason = INSUFFICIENT_HISTORY_REASON

    return write_backfill_report(
        status=status,
        reason=reason,
        required_trade_days=history_days,
        target_trade_days=dates,
        actual_trade_days=actual,
        fetched_trade_days=fetched,
        failed_trade_days=failed,
        ts_code=code,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill CNSV intraday 1min history through 14:00.")
    parser.add_argument("--history-days", type=int, default=int(os.getenv("CNSVDATA_INTRADAY_HISTORY_DAYS", DEFAULT_HISTORY_DAYS)))
    parser.add_argument("--end-date", default=os.getenv("CNSVDATA_INTRADAY_END_DATE", ""))
    parser.add_argument("--ts-code", default=os.getenv("CNSVDATA_TS_CODE", ""))
    args = parser.parse_args()
    report = backfill_intraday_1min_history(args.history_days, args.end_date, args.ts_code)
    print(json.dumps({"status": report["status"], "reason": report["reason"], "actual_trade_days": report["actual_trade_days"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
