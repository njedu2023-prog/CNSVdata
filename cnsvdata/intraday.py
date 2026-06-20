from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from cnsvdata.common import file_sha256, load_yaml, now_string, write_json, write_parquet
from cnsvdata.paths import DATA_DIR, METADATA_DIR, QUALITY_DIR, ROOT

ASOF_LABEL = "1400"
ASOF_TIME = "14:00:00"
ASOF_TIME_SHORT = "14:00"
DEFAULT_HISTORY_DAYS = 150
FEATURE_VERSION = "intraday_1400_v1"
LABEL_VERSION = "t1_close_vs_1400_v1"
MISSING_SOURCE_REASON = "missing_intraday_minute_source"
INSUFFICIENT_HISTORY_REASON = "insufficient_intraday_history"
FLAT_THRESHOLD = 0.002

INTRADAY_DIR = DATA_DIR / "intraday"
INTRADAY_RAW_DIR = INTRADAY_DIR / "raw"
INTRADAY_RAW_PATH = INTRADAY_RAW_DIR / "cnsv_1min_intraday_1400.parquet"
SNAPSHOT_ROOT = INTRADAY_DIR / "snapshots"
REPLAY_ROOT = INTRADAY_DIR / "replay"
INTRADAY_REFERENCE_ROOT = INTRADAY_DIR / "reference"
T1_REFERENCE_PATH = INTRADAY_REFERENCE_ROOT / "t1_close_reference.parquet"
TRADE_CALENDAR_REFERENCE_PATH = INTRADAY_REFERENCE_ROOT / "trade_calendar.parquet"
LABEL_ROOT = INTRADAY_DIR / "labels" / "t1_truth"
ML_ROOT = INTRADAY_DIR / "ml_dataset" / "t1_intraday"
PREVIEW_ROOT = INTRADAY_DIR / "preview"
INTRADAY_QUALITY_DIR = QUALITY_DIR / "intraday"
INTRADAY_METADATA_DIR = METADATA_DIR / "intraday"

PREDICTION_FORBIDDEN_NAMES = {
    "pred_up_prob", "pred_down_prob", "pred_return", "pred_price_low", "pred_price_mid",
    "pred_price_high", "model_confidence", "manual_decision_reference", "buy_signal",
    "sell_signal", "formal_signal",
}

MINUTE_COLUMNS = [
    "trade_date", "trade_time", "ts_code", "name", "open", "high", "low", "close",
    "volume", "amount", "source", "created_at", "pre_close", "avg_price", "vwap_cum",
    "ret_from_open", "ret_from_prev_min", "bar_index", "session",
]
AGG_COLUMNS = [
    "trade_date", "bar_start_time", "bar_end_time", "ts_code", "open", "high", "low",
    "close", "volume", "amount", "vwap", "bar_freq", "source_1min_count",
    "expected_1min_count", "missing_1min_count", "session", "created_at",
]
FEATURE_COLUMNS = [
    "feature_return_from_open_to_1400", "feature_return_from_vwap_to_1400",
    "feature_high_drawdown_until_1400", "feature_low_rebound_until_1400",
    "feature_intraday_volatility_until_1400", "feature_volume_until_1400",
    "feature_amount_until_1400", "feature_morning_volume_ratio",
    "feature_afternoon_volume_ratio", "feature_vwap_deviation", "feature_price_slope_morning",
    "feature_price_slope_afternoon", "feature_volume_slope_afternoon",
    "feature_range_until_1400", "feature_close_position_until_1400",
]
LABEL_COLUMNS = [
    "trade_date", "ts_code", "asof_time", "asof_price_1400", "next_trade_date",
    "next_close", "actual_return_vs_1400", "actual_up_label", "actual_down_label",
    "actual_flat_label", "actual_limitup_label", "truth_ready", "truth_status", "created_at",
]
TRAINSET_COLUMNS = [
    "trade_date", "ts_code", "asof_time", "asof_price_1400", "next_trade_date",
    "next_close", "actual_return_vs_1400", "actual_up_label", "actual_down_label",
    "actual_flat_label", "actual_limitup_label", *FEATURE_COLUMNS, "feature_version",
    "label_version", "created_at",
]


@dataclass(frozen=True)
class IntradayPaths:
    root: Path

    @property
    def one_min(self) -> Path:
        return self.root / "cnsv_1min_asof_1400.parquet"

    @property
    def five_min(self) -> Path:
        return self.root / "cnsv_5min_asof_1400.parquet"

    @property
    def fifteen_min(self) -> Path:
        return self.root / "cnsv_15min_asof_1400.parquet"

    @property
    def snapshot(self) -> Path:
        return self.root / "intraday_snapshot_1400.json"

    @property
    def quality(self) -> Path:
        return self.root / "intraday_quality_1400.json"

    @property
    def manifest(self) -> Path:
        return self.root / "intraday_manifest_1400.json"

    @property
    def ready(self) -> Path:
        return self.root / "intraday_ready_1400.json"


def compact_trade_date(value) -> str:
    text = str(value)
    return text[:10].replace("-", "") if len(text) >= 10 and text[4:5] == "-" else text[:8]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _target() -> dict:
    try:
        return load_yaml("target.yml").get("target", {})
    except Exception:
        return {"ts_code": "600150.SH", "name": ""}


def expected_minutes() -> list[str]:
    return (
        pd.date_range("09:30:00", "11:30:00", freq="min").strftime("%H:%M:%S").tolist()
        + pd.date_range("13:00:00", ASOF_TIME, freq="min").strftime("%H:%M:%S").tolist()
    )


def session_of_time(value: str) -> str:
    if "09:30:00" <= value <= "11:30:00":
        return "morning"
    if "13:00:00" <= value <= ASOF_TIME:
        return "afternoon"
    return "outside"


def snapshot_paths(trade_date: str, snapshot_type: str = "snapshots") -> IntradayPaths:
    root = SNAPSHOT_ROOT if snapshot_type == "snapshots" else REPLAY_ROOT
    return IntradayPaths(root / compact_trade_date(trade_date) / ASOF_LABEL)


def normalize_intraday_minutes(df: pd.DataFrame, source: str = "tushare") -> pd.DataFrame:
    frame = pd.DataFrame() if df is None else df.copy()
    if frame.empty:
        return pd.DataFrame(columns=MINUTE_COLUMNS)
    if "volume" not in frame.columns and "vol" in frame.columns:
        frame = frame.rename(columns={"vol": "volume"})
    if "trade_time" not in frame.columns and "trade_date" in frame.columns:
        frame = frame.rename(columns={"trade_date": "trade_time"})
    missing = [c for c in ["trade_time", "ts_code", "open", "high", "low", "close"] if c not in frame.columns]
    if missing:
        raise ValueError(f"intraday minute missing required columns: {missing}")

    frame["trade_time"] = pd.to_datetime(frame["trade_time"], errors="coerce")
    frame = frame.dropna(subset=["trade_time"]).copy()
    frame["trade_date"] = frame["trade_time"].dt.strftime("%Y%m%d")
    frame["time"] = frame["trade_time"].dt.strftime("%H:%M:%S")
    frame["session"] = frame["time"].map(session_of_time)
    frame = frame[(frame["session"] != "outside") & (frame["time"] <= ASOF_TIME)].copy()

    target = _target()
    frame["name"] = frame["name"] if "name" in frame.columns else target.get("name", "")
    frame["amount"] = frame["amount"] if "amount" in frame.columns else pd.NA
    frame["source"] = frame["source"] if "source" in frame.columns else source
    for column in ["open", "high", "low", "close", "volume", "amount"]:
        frame[column] = pd.to_numeric(frame.get(column, pd.NA), errors="coerce")
    if frame["amount"].isna().all():
        frame["amount"] = frame["close"] * frame["volume"]

    frame = frame.sort_values("trade_time").drop_duplicates("trade_time", keep="last").reset_index(drop=True)
    first_close = frame["close"].dropna().iloc[0] if not frame["close"].dropna().empty else pd.NA
    frame["created_at"] = now_string()
    frame["pre_close"] = pd.NA
    frame["avg_price"] = frame["amount"] / frame["volume"].replace(0, pd.NA)
    frame["vwap_cum"] = frame["amount"].cumsum() / frame["volume"].replace(0, pd.NA).cumsum()
    frame["ret_from_open"] = frame["close"] / first_close - 1 if pd.notna(first_close) and first_close else pd.NA
    frame["ret_from_prev_min"] = frame["close"].pct_change()
    frame["bar_index"] = range(1, len(frame) + 1)
    frame["trade_time"] = frame["trade_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return frame[MINUTE_COLUMNS]


def latest_150_trade_window(calendar_path: Path | None = None, history_days: int = DEFAULT_HISTORY_DAYS):
    path = calendar_path or TRADE_CALENDAR_REFERENCE_PATH
    if not path.exists():
        return "", "", []
    calendar = pd.read_parquet(path)
    column = "cal_date" if "cal_date" in calendar.columns else "trade_date"
    if column not in calendar.columns:
        return "", "", []
    if "is_open" in calendar.columns:
        calendar = calendar[pd.to_numeric(calendar["is_open"], errors="coerce") == 1]
    dates = sorted(calendar[column].dropna().astype(str).map(compact_trade_date).unique())[-history_days:]
    return (dates[0], dates[-1], dates) if dates else ("", "", [])


def select_latest_trade_date(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    dates = sorted(df["trade_date"].dropna().astype(str).map(compact_trade_date).unique())
    return dates[-1] if dates else ""


def read_source_minutes() -> pd.DataFrame:
    if not INTRADAY_RAW_PATH.exists():
        return pd.DataFrame(columns=MINUTE_COLUMNS)
    return normalize_intraday_minutes(pd.read_parquet(INTRADAY_RAW_PATH), source=INTRADAY_RAW_PATH.name)


def fetch_intraday_from_tushare(history_days: int = DEFAULT_HISTORY_DAYS) -> pd.DataFrame:
    from cnsvdata.tushare_client import call_with_retry, get_tushare_pro

    cfg = load_yaml("tushare.yml").get("tushare", {})
    start = os.getenv("CNSVDATA_INTRADAY_START_DATE", "")
    end = os.getenv("CNSVDATA_INTRADAY_END_DATE", "")
    if not start or not end:
        default_start, default_end, _ = latest_150_trade_window(history_days=history_days)
        start = start or default_start
        end = end or default_end
    params = {"ts_code": _target()["ts_code"], "freq": cfg.get("minute_freq", "1min")}
    if start:
        params["start_date"] = start
    if end:
        params["end_date"] = end
    return normalize_intraday_minutes(call_with_retry(get_tushare_pro().stk_mins, **params))


def write_latest_intraday_minutes(df: pd.DataFrame) -> Path:
    merged = normalize_intraday_minutes(df)
    if INTRADAY_RAW_PATH.exists():
        old = pd.read_parquet(INTRADAY_RAW_PATH)
        merged = normalize_intraday_minutes(pd.concat([old, merged], ignore_index=True), "merged")
    write_parquet(merged, INTRADAY_RAW_PATH)
    return INTRADAY_RAW_PATH


def build_missing_source_ready(reason: str = MISSING_SOURCE_REASON) -> dict:
    reasons = [reason]
    if INSUFFICIENT_HISTORY_REASON not in reasons:
        reasons.append(INSUFFICIENT_HISTORY_REASON)
    payload = {
        "line": "intraday_1400",
        "project": "CNSV intraday",
        "repo": "CNSVdata",
        "ready": False,
        "status": "FAIL",
        "reason": reasons,
        "blocking_reason": reason,
        "latest_snapshot_path": None,
        "quality_path": "data/quality/intraday/intraday_quality_latest.json",
        "manifest_path": "metadata/intraday/intraday_manifest_1400.json",
        "allowed_usage": {
            "can_run_daily_model": False,
            "can_run_intraday_model": False,
            "can_run_intraday_forecast": False,
            "can_train_model": False,
            "can_generate_formal_signal": False,
        },
        "created_at": now_string(),
    }
    write_json(payload, INTRADAY_METADATA_DIR / "intraday_ready_1400.json")
    write_json(intraday_downstream_contract(payload), INTRADAY_METADATA_DIR / "intraday_downstream_contract.json")
    write_json(
        {
            "line": "intraday_1400",
            "project": "CNSV intraday",
            "repo": "CNSVdata",
            "status": "FAIL",
            "trade_date": "",
            "asof_time": ASOF_TIME_SHORT,
            "snapshot_type": "missing_source",
            "generated_at": now_string(),
            "reason": reasons,
            "required_source": _display_path(INTRADAY_RAW_PATH),
            "files": [{"path": _display_path(INTRADAY_RAW_PATH), "exists": False, "status": "missing"}],
            "lineage": {"feature_window": "09:30-11:30,13:00-14:00", "future_data_guard": "trade_time <= 14:00"},
        },
        INTRADAY_METADATA_DIR / "intraday_manifest_1400.json",
    )
    write_json(
        {"line": "intraday_1400", "status": "FAIL", "reason": reasons, "generated_at": now_string()},
        INTRADAY_QUALITY_DIR / "intraday_quality_latest.json",
    )
    return payload


def aggregate_intraday_bars(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    rows = []
    for (trade_date, code, session), group in normalize_intraday_minutes(df).groupby(["trade_date", "ts_code", "session"], sort=True):
        group = group.sort_values("trade_time").reset_index(drop=True)
        for start in range(0, len(group), minutes):
            chunk = group.iloc[start:start + minutes]
            volume = chunk["volume"].sum()
            amount = chunk["amount"].sum()
            rows.append({
                "trade_date": trade_date,
                "bar_start_time": chunk["trade_time"].iloc[0],
                "bar_end_time": chunk["trade_time"].iloc[-1],
                "ts_code": code,
                "open": chunk["open"].iloc[0],
                "high": chunk["high"].max(),
                "low": chunk["low"].min(),
                "close": chunk["close"].iloc[-1],
                "volume": volume,
                "amount": amount,
                "vwap": amount / volume if volume else pd.NA,
                "bar_freq": f"{minutes}min",
                "source_1min_count": int(len(chunk)),
                "expected_1min_count": minutes,
                "missing_1min_count": int(max(minutes - len(chunk), 0)),
                "session": session,
                "created_at": now_string(),
            })
    return pd.DataFrame(rows, columns=AGG_COLUMNS)


def _slope(values: pd.Series):
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    return None if len(numeric) < 2 else float((numeric.iloc[-1] - numeric.iloc[0]) / (len(numeric) - 1))


def snapshot_summary(df: pd.DataFrame, snapshot_type: str = "snapshots") -> dict:
    minutes = normalize_intraday_minutes(df)
    target = _target()
    if minutes.empty:
        return {
            "trade_date": "",
            "ts_code": target.get("ts_code", ""),
            "name": target.get("name", ""),
            "asof_time": ASOF_TIME_SHORT,
            "asof_price_1400": None,
            "last_valid_trade_time": "",
            "minute_count_expected": len(expected_minutes()),
            "minute_count_actual": 0,
            "missing_minute_count": len(expected_minutes()),
            "snapshot_type": snapshot_type,
            "replay": snapshot_type == "replay",
            "created_at": now_string(),
            "source": "empty",
        }
    trade_date = select_latest_trade_date(minutes)
    minutes = minutes[minutes["trade_date"].astype(str).map(compact_trade_date) == trade_date]
    first = minutes.sort_values("trade_time").iloc[0]
    last = minutes.dropna(subset=["close"]).sort_values("trade_time").tail(1)
    close = last["close"].iloc[0] if not last.empty else pd.NA
    high = minutes["high"].max()
    low = minutes["low"].min()
    volume = minutes["volume"].sum()
    amount = minutes["amount"].sum()
    vwap = amount / volume if volume else pd.NA
    morning_volume = float(minutes.loc[minutes["session"] == "morning", "volume"].sum())
    afternoon_volume = float(minutes.loc[minutes["session"] == "afternoon", "volume"].sum())
    total_volume = morning_volume + afternoon_volume
    returns = pd.to_numeric(minutes["close"], errors="coerce").pct_change().dropna()
    missing = sorted(set(expected_minutes()) - set(minutes["trade_time"].str.slice(11, 19)))
    return {
        "trade_date": trade_date,
        "ts_code": str(first["ts_code"]),
        "name": str(first.get("name", "")),
        "asof_time": ASOF_TIME_SHORT,
        "asof_price_1400": float(close) if pd.notna(close) else None,
        "last_valid_trade_time": str(last["trade_time"].iloc[0]) if not last.empty else "",
        "open_0930": float(first["open"]),
        "high_until_1400": float(high),
        "low_until_1400": float(low),
        "close_asof_1400": float(close) if pd.notna(close) else None,
        "vwap_until_1400": float(vwap) if pd.notna(vwap) else None,
        "volume_until_1400": float(volume),
        "amount_until_1400": float(amount),
        "return_from_open_to_1400": float(close / first["open"] - 1) if pd.notna(close) and first["open"] else None,
        "return_from_vwap_to_1400": float(close / vwap - 1) if pd.notna(close) and pd.notna(vwap) and vwap else None,
        "high_drawdown_until_1400": float(close / high - 1) if pd.notna(close) and high else None,
        "low_rebound_until_1400": float(close / low - 1) if pd.notna(close) and low else None,
        "feature_intraday_volatility_until_1400": float(returns.std()) if not returns.empty else 0.0,
        "feature_morning_volume_ratio": morning_volume / total_volume if total_volume else None,
        "feature_afternoon_volume_ratio": afternoon_volume / total_volume if total_volume else None,
        "feature_price_slope_morning": _slope(minutes.loc[minutes["session"] == "morning", "close"]),
        "feature_price_slope_afternoon": _slope(minutes.loc[minutes["session"] == "afternoon", "close"]),
        "feature_volume_slope_afternoon": _slope(minutes.loc[minutes["session"] == "afternoon", "volume"]),
        "minute_count_expected": len(expected_minutes()),
        "minute_count_actual": int(len(minutes)),
        "missing_minute_count": int(len(missing)),
        "snapshot_type": snapshot_type,
        "replay": snapshot_type == "replay",
        "created_at": now_string(),
        "source": "intraday_1min_asof_1400",
    }


def quality_report(df: pd.DataFrame, snapshot_type: str = "snapshots") -> dict:
    checks = []

    def add(name: str, status: str, **extra) -> None:
        checks.append({"name": name, "status": status, **extra})

    try:
        minutes = normalize_intraday_minutes(df)
    except Exception as exc:
        return {"status": "FAIL", "generated_at": now_string(), "checks": [{"name": "schema_parse", "status": "FAIL", "detail": str(exc)}]}
    add("intraday_1min_exists", "PASS" if not minutes.empty else "FAIL", rows=int(len(minutes)))
    add("schema_complete", "PASS")
    if not minutes.empty:
        add("duplicate_minutes", "FAIL" if int(minutes.duplicated("trade_time").sum()) else "PASS")
        add("positive_prices", "FAIL" if len(minutes[(minutes[["open", "high", "low", "close"]] <= 0).any(axis=1)]) else "PASS")
        bad_ohlc = minutes[
            (minutes["high"] < minutes["low"]) | (minutes["open"] > minutes["high"]) | (minutes["open"] < minutes["low"])
            | (minutes["close"] > minutes["high"]) | (minutes["close"] < minutes["low"])
        ]
        add("ohlc_bounds", "FAIL" if len(bad_ohlc) else "PASS")
        add("non_negative_volume", "FAIL" if len(minutes[minutes["volume"] < 0]) else "PASS")
        missing = sorted(set(expected_minutes()) - set(minutes["trade_time"].str.slice(11, 19)))
        add("minute_window_coverage", "PASS" if not missing else "WARN", missing_minute_count=len(missing), missing_minutes=missing[:50])
        add("morning_window_present", "PASS" if (minutes["session"] == "morning").any() else "FAIL")
        add("afternoon_window_present", "PASS" if (minutes["session"] == "afternoon").any() else "FAIL")
        last = minutes.dropna(subset=["close"]).sort_values("trade_time").tail(1)
        last_time = str(last["trade_time"].iloc[0])[-8:] if not last.empty else ""
        add("asof_price_1400", "PASS" if not last.empty else "FAIL")
        add("last_valid_trade_time", "FAIL" if not last_time or last_time < "13:55:00" else ("WARN" if last_time < "13:59:00" else "PASS"), last_valid_time=last_time)
    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else ("WARN" if any(c["status"] == "WARN" for c in checks) else "PASS")
    return {
        "line": "intraday_1400",
        "status": status,
        "generated_at": now_string(),
        "asof_time": ASOF_TIME_SHORT,
        "snapshot_type": snapshot_type,
        "expected_minute_count": len(expected_minutes()),
        "checks": checks,
    }


def build_manifest(paths: IntradayPaths, trade_date: str, snapshot_type: str) -> dict:
    files = []
    for path in [paths.one_min, paths.five_min, paths.fifteen_min, paths.snapshot, paths.quality, paths.ready]:
        files.append({
            "path": _display_path(path),
            "exists": path.exists(),
            "file_size": path.stat().st_size if path.exists() else 0,
            "sha256": file_sha256(path) if path.exists() else "",
            "status": "present" if path.exists() else "missing",
        })
    return {
        "line": "intraday_1400",
        "project": "CNSV intraday",
        "repo": "CNSVdata",
        "trade_date": compact_trade_date(trade_date),
        "asof_time": ASOF_TIME_SHORT,
        "snapshot_type": snapshot_type,
        "generated_at": now_string(),
        "files": files,
        "lineage": {"feature_window": "09:30-11:30,13:00-14:00", "future_data_guard": "trade_time <= 14:00"},
    }


def ready_payload(paths: IntradayPaths, quality: dict, manifest: dict) -> dict:
    self_ready_path = _display_path(paths.ready) if hasattr(paths, "ready") else ""
    missing = [
        item["path"]
        for item in manifest.get("files", [])
        if not item.get("exists") and item.get("path") != self_ready_path
    ]
    status = "FAIL" if missing else quality.get("status", "FAIL")
    ready = status in {"PASS", "WARN"}
    reason = [check["name"] for check in quality.get("checks", []) if check.get("status") == "FAIL"]
    warnings = [check["name"] for check in quality.get("checks", []) if check.get("status") == "WARN"]
    if missing:
        reason.append("manifest_missing_files")
    snapshot_type = manifest.get("snapshot_type", "snapshots")
    replay = snapshot_type == "replay"
    return {
        "line": "intraday_1400",
        "project": "CNSV intraday",
        "repo": "CNSVdata",
        "ready": ready,
        "status": status,
        "trade_date": manifest.get("trade_date", ""),
        "asof_time": ASOF_TIME_SHORT,
        "snapshot_type": snapshot_type,
        "replay": replay,
        "reason": reason,
        "warnings": warnings,
        "blocking_reason": ";".join(reason) if not ready else None,
        "latest_snapshot_path": _display_path(paths.root) + "/",
        "quality_path": _display_path(paths.quality),
        "manifest_path": _display_path(paths.manifest),
        "allowed_usage": {
            "can_run_daily_model": False,
            "can_run_intraday_model": ready,
            "can_run_intraday_forecast": ready,
            "can_run_backtest": bool(ready and replay),
            "can_train_model": bool(ready and replay),
            "can_generate_formal_signal": False,
        },
        "created_at": now_string(),
    }


def write_snapshot_bundle(df: pd.DataFrame, trade_date: str, snapshot_type: str = "snapshots") -> dict:
    paths = snapshot_paths(trade_date, snapshot_type)
    paths.root.mkdir(parents=True, exist_ok=True)
    minutes = normalize_intraday_minutes(df)
    write_parquet(minutes, paths.one_min)
    write_parquet(aggregate_intraday_bars(minutes, 5), paths.five_min)
    write_parquet(aggregate_intraday_bars(minutes, 15), paths.fifteen_min)
    summary = snapshot_summary(minutes, snapshot_type)
    quality = quality_report(minutes, snapshot_type)
    write_json(summary, paths.snapshot)
    write_json(quality, paths.quality)
    manifest_probe = build_manifest(paths, trade_date, snapshot_type)
    ready = ready_payload(paths, quality, manifest_probe)
    write_json(ready, paths.ready)
    manifest = build_manifest(paths, trade_date, snapshot_type)
    write_json(manifest, paths.manifest)
    write_json(manifest, INTRADAY_METADATA_DIR / "intraday_manifest_1400.json")
    write_json(ready, INTRADAY_METADATA_DIR / "intraday_ready_1400.json")
    write_json(intraday_downstream_contract(ready), INTRADAY_METADATA_DIR / "intraday_downstream_contract.json")
    write_json(quality, INTRADAY_QUALITY_DIR / "intraday_quality_latest.json")
    return {"paths": paths, "summary": summary, "quality": quality, "manifest": manifest, "ready": ready}


def build_latest_snapshot_from_source() -> dict:
    minutes = read_source_minutes()
    trade_date = select_latest_trade_date(minutes)
    if not trade_date:
        raise SystemExit(build_missing_source_ready()["blocking_reason"])
    current = minutes[minutes["trade_date"].astype(str).map(compact_trade_date) == trade_date]
    return write_snapshot_bundle(current, trade_date, "snapshots")


def build_t1_reference_from_daily(daily_df: pd.DataFrame) -> pd.DataFrame:
    reference = daily_df.copy()
    if "ts_code" not in reference.columns:
        reference["ts_code"] = _target().get("ts_code", "600150.SH")
    reference["trade_date"] = reference["trade_date"].astype(str).map(compact_trade_date)
    reference = reference[["trade_date", "ts_code", "close"]].dropna(subset=["trade_date", "close"]).sort_values("trade_date")
    write_parquet(reference, T1_REFERENCE_PATH)
    return reference


def read_t1_reference() -> pd.DataFrame:
    if not T1_REFERENCE_PATH.exists():
        return pd.DataFrame(columns=["trade_date", "ts_code", "close"])
    reference = pd.read_parquet(T1_REFERENCE_PATH)
    reference["trade_date"] = reference["trade_date"].astype(str).map(compact_trade_date)
    if "ts_code" not in reference.columns:
        reference["ts_code"] = _target().get("ts_code", "600150.SH")
    return reference[["trade_date", "ts_code", "close"]].dropna(subset=["trade_date", "close"]).sort_values("trade_date")


def _snapshot_records() -> pd.DataFrame:
    rows = []
    for root in [REPLAY_ROOT, SNAPSHOT_ROOT]:
        if not root.exists():
            continue
        for path in root.glob("*/1400/intraday_snapshot_1400.json"):
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
    return pd.DataFrame(rows)


def build_t1_truth() -> pd.DataFrame:
    snapshots = _snapshot_records()
    reference = read_t1_reference()
    rows = []
    if not snapshots.empty and not reference.empty:
        for code, daily in reference.groupby("ts_code"):
            dates = daily.sort_values("trade_date")["trade_date"].tolist()
            close_map = daily.set_index("trade_date")["close"].to_dict()
            next_date = {date: dates[index + 1] for index, date in enumerate(dates[:-1])}
            code_snapshots = snapshots[snapshots.get("ts_code", code) == code]
            for _, snapshot in code_snapshots.iterrows():
                trade_date = compact_trade_date(snapshot.get("trade_date", ""))
                asof_price = pd.to_numeric(snapshot.get("asof_price_1400"), errors="coerce")
                next_trade_date = next_date.get(trade_date, "")
                next_close = close_map.get(next_trade_date) if next_trade_date else None
                ready = bool(next_trade_date and pd.notna(asof_price) and pd.notna(next_close))
                actual_return = next_close / asof_price - 1 if ready and asof_price else pd.NA
                rows.append({
                    "trade_date": trade_date,
                    "ts_code": code,
                    "asof_time": ASOF_TIME_SHORT,
                    "asof_price_1400": asof_price,
                    "next_trade_date": next_trade_date,
                    "next_close": next_close if ready else pd.NA,
                    "actual_return_vs_1400": actual_return,
                    "actual_up_label": int(actual_return > 0) if pd.notna(actual_return) else pd.NA,
                    "actual_down_label": int(actual_return < 0) if pd.notna(actual_return) else pd.NA,
                    "actual_flat_label": int(abs(actual_return) <= FLAT_THRESHOLD) if pd.notna(actual_return) else pd.NA,
                    "actual_limitup_label": int(actual_return >= 0.099) if pd.notna(actual_return) else pd.NA,
                    "truth_ready": ready,
                    "truth_status": "PASS" if ready else "WARN",
                    "created_at": now_string(),
                })
    truth = pd.DataFrame(rows, columns=LABEL_COLUMNS)
    LABEL_ROOT.mkdir(parents=True, exist_ok=True)
    write_parquet(truth, LABEL_ROOT / "t1_truth_vs_1400_latest.parquet")
    truth.to_csv(LABEL_ROOT / "t1_truth_vs_1400_latest.csv", index=False, encoding="utf-8-sig")
    write_json({
        "line": "intraday_1400",
        "status": "PASS" if not truth.empty and truth["truth_ready"].any() else "WARN",
        "rows": int(len(truth)),
        "ready_rows": int(truth["truth_ready"].sum()) if not truth.empty else 0,
        "reference_path": "data/intraday/reference/t1_close_reference.parquet",
        "generated_at": now_string(),
    }, LABEL_ROOT / "t1_truth_quality.json")
    write_json({
        "line": "intraday_1400",
        "label_version": LABEL_VERSION,
        "reference_path": "data/intraday/reference/t1_close_reference.parquet",
        "outputs": [
            "data/intraday/labels/t1_truth/t1_truth_vs_1400_latest.parquet",
            "data/intraday/labels/t1_truth/t1_truth_vs_1400_latest.csv",
            "data/intraday/labels/t1_truth/t1_truth_manifest.json",
            "data/intraday/labels/t1_truth/t1_truth_quality.json",
        ],
        "rows": int(len(truth)),
        "ready_rows": int(truth["truth_ready"].sum()) if not truth.empty else 0,
        "created_at": now_string(),
    }, LABEL_ROOT / "t1_truth_manifest.json")
    return truth


def check_trainset_no_future_leak(trainset: pd.DataFrame) -> dict:
    columns = set(trainset.columns)
    forbidden = sorted(columns & PREDICTION_FORBIDDEN_NAMES)
    bad_features = [c for c in trainset.columns if c.startswith("feature_") and any(x in c for x in ["next_", "actual_", "label", "created_at"])]
    checks = [
        {"name": "no_prediction_columns", "status": "FAIL" if forbidden else "PASS", "forbidden_columns": forbidden},
        {"name": "feature_names_no_label_or_future", "status": "FAIL" if bad_features else "PASS", "bad_feature_columns": bad_features},
        {"name": "feature_version_present", "status": "PASS" if "feature_version" in columns else "FAIL"},
        {"name": "label_version_present", "status": "PASS" if "label_version" in columns else "FAIL"},
        {"name": "professional_feature_columns_present", "status": "PASS" if set(FEATURE_COLUMNS).issubset(columns) else "FAIL"},
    ]
    return {
        "line": "intraday_1400",
        "status": "FAIL" if any(check["status"] == "FAIL" for check in checks) else "PASS",
        "generated_at": now_string(),
        "rows": int(len(trainset)),
        "checks": checks,
    }


def _snapshot_feature_row(snapshot: pd.Series | dict) -> dict:
    get = snapshot.get
    asof_price = pd.to_numeric(get("asof_price_1400"), errors="coerce")
    open_price = pd.to_numeric(get("open_0930"), errors="coerce")
    high = pd.to_numeric(get("high_until_1400"), errors="coerce")
    low = pd.to_numeric(get("low_until_1400"), errors="coerce")
    vwap = pd.to_numeric(get("vwap_until_1400"), errors="coerce")
    volume = pd.to_numeric(get("volume_until_1400"), errors="coerce")
    amount = pd.to_numeric(get("amount_until_1400"), errors="coerce")
    def safe(value, default=0.0):
        return float(value) if pd.notna(value) else default
    return {
        "feature_return_from_open_to_1400": safe(get("return_from_open_to_1400")),
        "feature_return_from_vwap_to_1400": safe(get("return_from_vwap_to_1400")),
        "feature_high_drawdown_until_1400": safe(get("high_drawdown_until_1400")),
        "feature_low_rebound_until_1400": safe(get("low_rebound_until_1400")),
        "feature_intraday_volatility_until_1400": safe(get("feature_intraday_volatility_until_1400")),
        "feature_volume_until_1400": safe(volume),
        "feature_amount_until_1400": safe(amount),
        "feature_morning_volume_ratio": safe(get("feature_morning_volume_ratio")),
        "feature_afternoon_volume_ratio": safe(get("feature_afternoon_volume_ratio")),
        "feature_vwap_deviation": safe(asof_price / vwap - 1 if pd.notna(asof_price) and pd.notna(vwap) and vwap else pd.NA),
        "feature_price_slope_morning": safe(get("feature_price_slope_morning")),
        "feature_price_slope_afternoon": safe(get("feature_price_slope_afternoon")),
        "feature_volume_slope_afternoon": safe(get("feature_volume_slope_afternoon")),
        "feature_range_until_1400": safe((high - low) / open_price if pd.notna(high) and pd.notna(low) and pd.notna(open_price) and open_price else pd.NA),
        "feature_close_position_until_1400": safe((asof_price - low) / (high - low) if pd.notna(asof_price) and pd.notna(high) and pd.notna(low) and high != low else pd.NA),
    }


def build_t1_intraday_trainset() -> pd.DataFrame:
    truth_path = LABEL_ROOT / "t1_truth_vs_1400_latest.parquet"
    truth = pd.read_parquet(truth_path) if truth_path.exists() else build_t1_truth()
    snapshots = _snapshot_records()
    snapshot_map = {}
    if not snapshots.empty:
        for _, snapshot in snapshots.iterrows():
            key = (compact_trade_date(snapshot.get("trade_date", "")), snapshot.get("ts_code", _target().get("ts_code", "600150.SH")))
            snapshot_map[key] = snapshot
    rows = []
    for _, row in truth.iterrows():
        if not bool(row.get("truth_ready")):
            continue
        record = {column: row.get(column) for column in LABEL_COLUMNS if column not in {"truth_ready", "truth_status"}}
        key = (compact_trade_date(row.get("trade_date", "")), row.get("ts_code", _target().get("ts_code", "600150.SH")))
        record.update(_snapshot_feature_row(snapshot_map.get(key, {})))
        record.update({"feature_version": FEATURE_VERSION, "label_version": LABEL_VERSION, "created_at": now_string()})
        rows.append(record)
    trainset = pd.DataFrame(rows, columns=TRAINSET_COLUMNS)
    ML_ROOT.mkdir(parents=True, exist_ok=True)
    write_parquet(trainset, ML_ROOT / "t1_intraday_trainset.parquet")
    trainset.to_csv(ML_ROOT / "t1_intraday_trainset_latest.csv", index=False, encoding="utf-8-sig")
    write_json({
        "line": "intraday_1400",
        "feature_version": FEATURE_VERSION,
        "feature_columns": FEATURE_COLUMNS,
        "feature_source": "data/intraday/snapshots_or_replay/*/1400/intraday_snapshot_1400.json",
        "forbidden_feature_inputs": [
            "next_close", "actual_return_vs_1400", "actual_up_label", "actual_down_label",
            "actual_flat_label", "actual_limitup_label", "created_at", "formal_signal",
        ],
        "created_at": now_string(),
    }, ML_ROOT / "feature_manifest.json")
    write_json({
        "line": "intraday_1400",
        "label_version": LABEL_VERSION,
        "label_columns": [c for c in LABEL_COLUMNS if c not in {"truth_ready", "truth_status", "created_at"}],
        "created_at": now_string(),
    }, ML_ROOT / "label_manifest.json")
    write_json(check_trainset_no_future_leak(trainset), ML_ROOT / "trainset_quality.json")
    return trainset


def _write_replay_metadata_ready(latest_ready: dict, replay_summary: dict, history_days: int) -> dict:
    top_ready = dict(latest_ready)
    actual = int(replay_summary.get("actual_trade_days", 0))
    reason = list(top_ready.get("reason") or [])
    if actual < history_days and INSUFFICIENT_HISTORY_REASON not in reason:
        reason.append(INSUFFICIENT_HISTORY_REASON)
    if actual < history_days and top_ready.get("ready"):
        top_ready["status"] = "WARN"
        top_ready["ready"] = True
        top_ready["blocking_reason"] = None
    elif reason:
        top_ready["blocking_reason"] = ";".join(reason) if not top_ready.get("ready") else None
    top_ready["reason"] = reason
    top_ready["history_days_required"] = int(history_days)
    top_ready["actual_trade_days"] = actual
    top_ready["generated_snapshots"] = int(replay_summary.get("generated_snapshots", actual))
    top_ready.setdefault("warnings", [])
    top_ready["allowed_usage"] = {
        "can_run_daily_model": False,
        "can_run_intraday_model": bool(top_ready.get("ready")),
        "can_run_intraday_forecast": bool(top_ready.get("ready")),
        "can_run_backtest": bool(top_ready.get("ready")),
        "can_train_model": bool(top_ready.get("ready") and actual >= history_days),
        "can_generate_formal_signal": False,
    }
    write_json(top_ready, INTRADAY_METADATA_DIR / "intraday_ready_1400.json")
    write_json(intraday_downstream_contract(top_ready), INTRADAY_METADATA_DIR / "intraday_downstream_contract.json")
    return top_ready


def replay_intraday_history(history_days: int = DEFAULT_HISTORY_DAYS) -> dict:
    source = read_source_minutes()
    if source.empty:
        payload = {
            "line": "intraday_1400",
            "status": "FAIL",
            "generated_at": now_string(),
            "history_days_required": history_days,
            "required_trade_days": history_days,
            "actual_trade_days": 0,
            "generated_snapshots": 0,
            "reason": INSUFFICIENT_HISTORY_REASON,
            "blocking_reason": MISSING_SOURCE_REASON,
            "can_train_model": False,
            "source": "tushare",
        }
        write_json(payload, INTRADAY_QUALITY_DIR / "intraday_replay_latest.json")
        build_missing_source_ready()
        return payload
    generated = []
    latest_ready = {}
    dates = sorted(source["trade_date"].dropna().astype(str).map(compact_trade_date).unique())[-history_days:]
    for trade_date in dates:
        bundle = write_snapshot_bundle(source[source["trade_date"].astype(str).map(compact_trade_date) == trade_date], trade_date, "replay")
        generated.append({"trade_date": trade_date, "status": bundle["quality"]["status"], "path": _display_path(bundle["paths"].root)})
        latest_ready = bundle["ready"]
    actual = len(generated)
    payload = {
        "line": "intraday_1400",
        "status": "PASS" if actual >= history_days else "WARN",
        "generated_at": now_string(),
        "history_days_required": history_days,
        "required_trade_days": history_days,
        "actual_trade_days": actual,
        "generated_snapshots": actual,
        "reason": None if actual >= history_days else INSUFFICIENT_HISTORY_REASON,
        "can_train_model": actual >= history_days,
        "source": "intraday_raw",
        "snapshots": generated,
    }
    write_json(payload, INTRADAY_QUALITY_DIR / "intraday_replay_latest.json")
    if latest_ready:
        _write_replay_metadata_ready(latest_ready, payload, history_days)
    build_t1_truth()
    build_t1_intraday_trainset()
    return payload


def build_intraday_preview_csv() -> Path:
    source = read_source_minutes()
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    path = PREVIEW_ROOT / "intraday_1400_preview.csv"
    source.tail(200).to_csv(path, index=False, encoding="utf-8-sig")
    return path


def intraday_downstream_contract(ready: dict | None = None) -> dict:
    ready = ready or {}
    return {
        "line": "intraday_1400",
        "provider_repo": "CNSVdata",
        "consumer_repo": "CNSV",
        "consumer_program": "CNSV_intraday_main",
        "ready_path": "metadata/intraday/intraday_ready_1400.json",
        "manifest_path": "metadata/intraday/intraday_manifest_1400.json",
        "can_run_daily_model": False,
        "can_run_intraday_model": bool(ready.get("ready", False)),
        "can_generate_formal_signal": False,
        "created_at": now_string(),
    }


def intraday_acceptance_report() -> dict:
    ready_path = INTRADAY_METADATA_DIR / "intraday_ready_1400.json"
    ready = json.loads(ready_path.read_text(encoding="utf-8")) if ready_path.exists() else build_missing_source_ready()
    replay_path = INTRADAY_QUALITY_DIR / "intraday_replay_latest.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8")) if replay_path.exists() else {}
    checks = [
        {"name": "ready_exists", "status": "PASS" if ready_path.exists() else "FAIL"},
        {"name": "raw_exists", "status": "PASS" if INTRADAY_RAW_PATH.exists() else "FAIL", "reason": None if INTRADAY_RAW_PATH.exists() else MISSING_SOURCE_REASON},
        {"name": "downstream_contract_exists", "status": "PASS" if (INTRADAY_METADATA_DIR / "intraday_downstream_contract.json").exists() else "WARN"},
        {"name": "manifest_exists", "status": "PASS" if (INTRADAY_METADATA_DIR / "intraday_manifest_1400.json").exists() else "FAIL"},
        {"name": "replay_history", "status": "PASS" if replay.get("actual_trade_days", 0) >= DEFAULT_HISTORY_DAYS else "WARN", "reason": None if replay.get("actual_trade_days", 0) >= DEFAULT_HISTORY_DAYS else INSUFFICIENT_HISTORY_REASON},
        {"name": "t1_truth_exists", "status": "PASS" if (LABEL_ROOT / "t1_truth_vs_1400_latest.parquet").exists() else "WARN"},
        {"name": "t1_truth_manifest_exists", "status": "PASS" if (LABEL_ROOT / "t1_truth_manifest.json").exists() else "WARN"},
        {"name": "trainset_exists", "status": "PASS" if (ML_ROOT / "t1_intraday_trainset.parquet").exists() else "WARN"},
        {"name": "feature_manifest_exists", "status": "PASS" if (ML_ROOT / "feature_manifest.json").exists() else "WARN"},
        {"name": "label_manifest_exists", "status": "PASS" if (ML_ROOT / "label_manifest.json").exists() else "WARN"},
        {"name": "formal_signal_disabled", "status": "PASS"},
    ]
    if (ML_ROOT / "t1_intraday_trainset.parquet").exists():
        trainset = pd.read_parquet(ML_ROOT / "t1_intraday_trainset.parquet")
        checks.extend(check_trainset_no_future_leak(trainset)["checks"])
    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else ("WARN" if any(c["status"] == "WARN" for c in checks) else "PASS")
    report = {"line": "intraday_1400", "status": status, "generated_at": now_string(), "checks": checks, "ready": ready}
    write_json(report, INTRADAY_QUALITY_DIR / "intraday_acceptance_latest.json")
    return report


def intraday_smoke_read() -> dict:
    ready_path = INTRADAY_METADATA_DIR / "intraday_ready_1400.json"
    if not ready_path.exists():
        payload = {"line": "intraday_1400", "status": "FAIL", "reason": "missing_intraday_ready", "generated_at": now_string(), "formal_signal": False}
    else:
        ready = json.loads(ready_path.read_text(encoding="utf-8"))
        payload = {
            "line": "intraday_1400",
            "status": "PASS" if ready.get("ready") else "FAIL",
            "reason": ready.get("reason", []),
            "generated_at": now_string(),
            "formal_signal": False,
        }
    write_json(payload, INTRADAY_QUALITY_DIR / "intraday_smoke_latest.json")
    return payload
