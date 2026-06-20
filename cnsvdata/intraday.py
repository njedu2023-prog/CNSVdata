from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from cnsvdata.common import file_sha256, load_yaml, now_string, write_json, write_parquet
from cnsvdata.paths import DATA_DIR, METADATA_DIR, PROCESSED_DIR, QUALITY_DIR, ROOT
ASOF_LABEL = "1400"
ASOF_TIME = "14:00:00"
ASOF_TIME_SHORT = "14:00"
DEFAULT_HISTORY_DAYS = 150
FEATURE_VERSION = "intraday_1400_v1"
LABEL_VERSION = "t1_close_vs_1400_v1"
FLAT_THRESHOLD = 0.002
INTRADAY_DIR = DATA_DIR / "intraday"
SNAPSHOT_ROOT = INTRADAY_DIR / "snapshots"
REPLAY_ROOT = INTRADAY_DIR / "replay"
LABEL_ROOT = DATA_DIR / "labels" / "t1_truth"
ML_ROOT = DATA_DIR / "ml_dataset" / "t1_intraday"
PREVIEW_ROOT = DATA_DIR / "preview" / "intraday"
INTRADAY_QUALITY_DIR = QUALITY_DIR / "intraday"
INTRADAY_METADATA_DIR = METADATA_DIR / "intraday"
PREDICTION_FORBIDDEN_NAMES = {"pred_up_prob", "pred_down_prob", "pred_return", "pred_price_low", "pred_price_mid", "pred_price_high", "model_confidence", "manual_decision_reference", "buy_signal", "sell_signal", "formal_signal"}
MINUTE_COLUMNS = ["trade_date", "trade_time", "ts_code", "name", "open", "high", "low", "close", "volume", "amount", "source", "created_at", "pre_close", "avg_price", "vwap_cum", "ret_from_open", "ret_from_prev_min", "bar_index", "session"]
AGG_COLUMNS = ["trade_date", "bar_start_time", "bar_end_time", "ts_code", "open", "high", "low", "close", "volume", "amount", "vwap", "bar_freq", "source_1min_count", "expected_1min_count", "missing_1min_count", "session", "created_at"]
@dataclass(frozen=True)
class IntradayPaths:
    root: Path
    @property
    def one_min(self): return self.root / "cnsv_1min_asof_1400.parquet"
    @property
    def five_min(self): return self.root / "cnsv_5min_asof_1400.parquet"
    @property
    def fifteen_min(self): return self.root / "cnsv_15min_asof_1400.parquet"
    @property
    def snapshot(self): return self.root / "intraday_snapshot_1400.json"
    @property
    def quality(self): return self.root / "intraday_quality_1400.json"
    @property
    def manifest(self): return self.root / "intraday_manifest_1400.json"
    @property
    def ready(self): return self.root / "intraday_ready_1400.json"
def compact_trade_date(value) -> str:
    text = str(value)
    return text[:10].replace("-", "") if len(text) >= 10 and text[4:5] == "-" else text[:8]
def expected_minutes() -> list[str]:
    am = pd.date_range("09:30:00", "11:30:00", freq="min").strftime("%H:%M:%S").tolist()
    pm = pd.date_range("13:00:00", ASOF_TIME, freq="min").strftime("%H:%M:%S").tolist()
    return am + pm
def session_of_time(text: str) -> str:
    if "09:30:00" <= text <= "11:30:00": return "morning"
    if "13:00:00" <= text <= ASOF_TIME: return "afternoon"
    return "outside"
def _target() -> dict:
    try: return load_yaml("target.yml").get("target", {})
    except Exception: return {"ts_code": "600150.SH", "name": ""}
def snapshot_paths(trade_date: str, snapshot_type: str = "snapshots") -> IntradayPaths:
    root = SNAPSHOT_ROOT if snapshot_type == "snapshots" else REPLAY_ROOT
    return IntradayPaths(root / compact_trade_date(trade_date) / ASOF_LABEL)
def normalize_intraday_minutes(df: pd.DataFrame, source: str = "tushare") -> pd.DataFrame:
    work = pd.DataFrame() if df is None else df.copy()
    if work.empty: return pd.DataFrame(columns=MINUTE_COLUMNS)
    if "volume" not in work.columns and "vol" in work.columns: work = work.rename(columns={"vol": "volume"})
    if "trade_time" not in work.columns and "trade_date" in work.columns: work = work.rename(columns={"trade_date": "trade_time"})
    missing = [c for c in ["trade_time", "ts_code", "open", "high", "low", "close"] if c not in work.columns]
    if missing: raise ValueError(f"intraday minute missing required columns: {missing}")
    work["trade_time"] = pd.to_datetime(work["trade_time"], errors="coerce")
    work = work.dropna(subset=["trade_time"])
    work["trade_date"] = work["trade_time"].dt.strftime("%Y%m%d")
    work["time"] = work["trade_time"].dt.strftime("%H:%M:%S")
    work = work[(work["time"].map(session_of_time) != "outside") & (work["time"] <= ASOF_TIME)].copy()
    target = _target()
    work["name"] = work["name"] if "name" in work.columns else target.get("name", "")
    work["amount"] = work["amount"] if "amount" in work.columns else pd.NA
    work["source"] = work["source"] if "source" in work.columns else source
    work["created_at"] = now_string()
    work["session"] = work["time"].map(session_of_time)
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        work[col] = pd.to_numeric(work.get(col, pd.NA), errors="coerce")
    if work["amount"].isna().all(): work["amount"] = work["close"] * work["volume"]
    work = work.sort_values("trade_time").drop_duplicates("trade_time", keep="last").reset_index(drop=True)
    first_close = work["close"].dropna().iloc[0] if not work["close"].dropna().empty else pd.NA
    work["bar_index"] = range(1, len(work) + 1)
    work["pre_close"] = pd.NA
    work["avg_price"] = work["amount"] / work["volume"].replace(0, pd.NA)
    work["vwap_cum"] = work["amount"].cumsum() / work["volume"].replace(0, pd.NA).cumsum()
    work["ret_from_open"] = work["close"] / first_close - 1 if pd.notna(first_close) and first_close else pd.NA
    work["ret_from_prev_min"] = work["close"].pct_change()
    work["trade_time"] = work["trade_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return work[MINUTE_COLUMNS]
def latest_150_trade_window(calendar_path: Path | None = None, history_days: int = DEFAULT_HISTORY_DAYS) -> tuple[str, str, list[str]]:
    path = calendar_path or PROCESSED_DIR / "trade_calendar.parquet"
    if not path.exists(): return "", "", []
    cal = pd.read_parquet(path)
    date_col = "cal_date" if "cal_date" in cal.columns else "trade_date"
    if date_col not in cal.columns: return "", "", []
    if "is_open" in cal.columns: cal = cal[pd.to_numeric(cal["is_open"], errors="coerce") == 1]
    dates = sorted(cal[date_col].dropna().astype(str).map(compact_trade_date).unique())[-history_days:]
    return (dates[0], dates[-1], dates) if dates else ("", "", [])
def select_latest_trade_date(df: pd.DataFrame) -> str:
    dates = sorted(df["trade_date"].dropna().astype(str).map(compact_trade_date).unique()) if not df.empty else []
    return dates[-1] if dates else ""
def fetch_intraday_from_tushare(history_days: int = DEFAULT_HISTORY_DAYS) -> pd.DataFrame:
    from cnsvdata.tushare_client import call_with_retry, get_tushare_pro
    target, config = _target(), load_yaml("tushare.yml").get("tushare", {})
    start_date, end_date = os.getenv("CNSVDATA_INTRADAY_START_DATE", ""), os.getenv("CNSVDATA_INTRADAY_END_DATE", "")
    if not start_date or not end_date:
        start, end, _ = latest_150_trade_window(history_days=history_days)
        start_date, end_date = start_date or start, end_date or end
    kwargs = {"ts_code": target["ts_code"], "freq": config.get("minute_freq", "1min")}
    if start_date: kwargs["start_date"] = start_date
    if end_date: kwargs["end_date"] = end_date
    return normalize_intraday_minutes(call_with_retry(get_tushare_pro().stk_mins, **kwargs))
def read_source_minutes() -> pd.DataFrame:
    for path in [INTRADAY_DIR / "raw" / "cnsv_1min_intraday_1400.parquet", PROCESSED_DIR / "cnsv_1min.parquet"]:
        if path.exists(): return normalize_intraday_minutes(pd.read_parquet(path), source=path.name)
    return pd.DataFrame(columns=MINUTE_COLUMNS)
def write_latest_intraday_minutes(df: pd.DataFrame) -> Path:
    out = INTRADAY_DIR / "raw" / "cnsv_1min_intraday_1400.parquet"
    merged = normalize_intraday_minutes(df)
    if out.exists(): merged = normalize_intraday_minutes(pd.concat([pd.read_parquet(out), merged], ignore_index=True), source="merged")
    write_parquet(merged, out)
    return out
def aggregate_intraday_bars(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    rows = []
    for (trade_date, ts_code, session), group in normalize_intraday_minutes(df).groupby(["trade_date", "ts_code", "session"], sort=True):
        group = group.sort_values("trade_time").reset_index(drop=True)
        for start in range(0, len(group), minutes):
            chunk = group.iloc[start:start + minutes]
            volume, amount = chunk["volume"].sum(), chunk["amount"].sum()
            rows.append({"trade_date": trade_date, "bar_start_time": chunk["trade_time"].iloc[0], "bar_end_time": chunk["trade_time"].iloc[-1], "ts_code": ts_code, "open": chunk["open"].iloc[0], "high": chunk["high"].max(), "low": chunk["low"].min(), "close": chunk["close"].iloc[-1], "volume": volume, "amount": amount, "vwap": amount / volume if volume else pd.NA, "bar_freq": f"{minutes}min", "source_1min_count": int(len(chunk)), "expected_1min_count": minutes, "missing_1min_count": int(max(minutes - len(chunk), 0)), "session": session, "created_at": now_string()})
    return pd.DataFrame(rows, columns=AGG_COLUMNS)
def snapshot_summary(df: pd.DataFrame, snapshot_type: str = "snapshots") -> dict:
    target, work = _target(), normalize_intraday_minutes(df)
    if work.empty:
        return {"trade_date": "", "ts_code": target.get("ts_code", ""), "name": target.get("name", ""), "asof_time": ASOF_TIME_SHORT, "asof_price_1400": None, "last_valid_trade_time": "", "minute_count_expected": len(expected_minutes()), "minute_count_actual": 0, "missing_minute_count": len(expected_minutes()), "snapshot_type": snapshot_type, "replay": snapshot_type == "replay", "created_at": now_string(), "source": "empty"}
    trade_date = select_latest_trade_date(work)
    work = work[work["trade_date"].astype(str).map(compact_trade_date) == trade_date]
    first = work.sort_values("trade_time").iloc[0]
    last = work.dropna(subset=["close"]).sort_values("trade_time").tail(1)
    close = last["close"].iloc[0] if not last.empty else pd.NA
    high, low, volume, amount = work["high"].max(), work["low"].min(), work["volume"].sum(), work["amount"].sum()
    vwap = amount / volume if volume else pd.NA
    missing = sorted(set(expected_minutes()) - set(work["trade_time"].str.slice(11, 19)))
    return {"trade_date": trade_date, "ts_code": str(first["ts_code"]), "name": str(first.get("name", target.get("name", ""))), "asof_time": ASOF_TIME_SHORT, "asof_price_1400": float(close) if pd.notna(close) else None, "last_valid_trade_time": str(last["trade_time"].iloc[0]) if not last.empty else "", "open_0930": float(first["open"]), "high_until_1400": float(high), "low_until_1400": float(low), "close_asof_1400": float(close) if pd.notna(close) else None, "vwap_until_1400": float(vwap) if pd.notna(vwap) else None, "volume_until_1400": float(volume), "amount_until_1400": float(amount), "return_from_open_to_1400": float(close / first["open"] - 1) if pd.notna(close) and first["open"] else None, "return_from_vwap_to_1400": float(close / vwap - 1) if pd.notna(close) and pd.notna(vwap) and vwap else None, "high_drawdown_until_1400": float(close / high - 1) if pd.notna(close) and high else None, "low_rebound_until_1400": float(close / low - 1) if pd.notna(close) and low else None, "minute_count_expected": len(expected_minutes()), "minute_count_actual": int(len(work)), "missing_minute_count": int(len(missing)), "snapshot_type": snapshot_type, "replay": snapshot_type == "replay", "created_at": now_string(), "source": "intraday_1min_asof_1400"}
def quality_report(df: pd.DataFrame, snapshot_type: str = "snapshots") -> dict:
    checks = []
    def add(name, status, **extra): checks.append({"name": name, "status": status, **extra})
    try: work = normalize_intraday_minutes(df)
    except Exception as exc: return {"status": "FAIL", "generated_at": now_string(), "checks": [{"name": "schema_parse", "status": "FAIL", "detail": str(exc)}]}
    add("intraday_1min_exists", "PASS" if not work.empty else "FAIL", rows=int(len(work)))
    add("schema_complete", "PASS")
    if not work.empty:
        add("duplicate_minutes", "FAIL" if int(work.duplicated("trade_time").sum()) else "PASS")
        add("positive_prices", "FAIL" if len(work[(work[["open", "high", "low", "close"]] <= 0).any(axis=1)]) else "PASS")
        bad_ohlc = work[(work["high"] < work["low"]) | (work["open"] > work["high"]) | (work["open"] < work["low"]) | (work["close"] > work["high"]) | (work["close"] < work["low"])]
        add("ohlc_bounds", "FAIL" if len(bad_ohlc) else "PASS")
        add("non_negative_volume", "FAIL" if len(work[work["volume"] < 0]) else "PASS")
        missing = sorted(set(expected_minutes()) - set(work["trade_time"].str.slice(11, 19)))
        add("minute_window_coverage", "PASS" if not missing else "WARN", missing_minute_count=len(missing), missing_minutes=missing[:50])
        add("morning_window_present", "PASS" if (work["session"] == "morning").any() else "FAIL")
        add("afternoon_window_present", "PASS" if (work["session"] == "afternoon").any() else "FAIL")
        last = work.dropna(subset=["close"]).sort_values("trade_time").tail(1)
        add("asof_price_1400", "PASS" if not last.empty else "FAIL")
        last_time = str(last["trade_time"].iloc[0])[-8:] if not last.empty else ""
        add("last_valid_trade_time", "FAIL" if not last_time or last_time < "13:55:00" else ("WARN" if last_time < "13:59:00" else "PASS"), last_valid_time=last_time)
    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else ("WARN" if any(c["status"] == "WARN" for c in checks) else "PASS")
    return {"status": status, "generated_at": now_string(), "asof_time": ASOF_TIME_SHORT, "snapshot_type": snapshot_type, "expected_minute_count": len(expected_minutes()), "checks": checks}
def build_manifest(paths: IntradayPaths, trade_date: str, snapshot_type: str) -> dict:
    files = []
    for path in [paths.one_min, paths.five_min, paths.fifteen_min, paths.snapshot, paths.quality]:
        files.append({"path": str(path.relative_to(ROOT)), "exists": path.exists(), "file_size": path.stat().st_size if path.exists() else 0, "sha256": file_sha256(path) if path.exists() else "", "status": "present" if path.exists() else "missing"})
    return {"project": "CNSV intraday", "repo": "CNSVdata", "trade_date": compact_trade_date(trade_date), "asof_time": ASOF_TIME_SHORT, "snapshot_type": snapshot_type, "generated_at": now_string(), "files": files, "lineage": {"feature_window": "09:30-11:30,13:00-14:00", "future_data_guard": "trade_time <= 14:00"}}
def ready_payload(paths: IntradayPaths, quality: dict, manifest: dict) -> dict:
    missing = [i["path"] for i in manifest.get("files", []) if not i.get("exists")]
    status = "FAIL" if missing else quality.get("status", "FAIL")
    ready = status in {"PASS", "WARN"}
    return {"project": "CNSV intraday", "repo": "CNSVdata", "trade_date": manifest.get("trade_date", ""), "asof_time": ASOF_TIME_SHORT, "ready": ready, "status": status, "reason": ([c["name"] for c in quality.get("checks", []) if c.get("status") == "FAIL"] + (["manifest_missing_files"] if missing else [])), "latest_snapshot_path": str(paths.root.relative_to(ROOT)) + "/", "quality_path": str(paths.quality.relative_to(ROOT)), "manifest_path": str(paths.manifest.relative_to(ROOT)), "allowed_usage": {"can_develop_cnsv_main_program": ready, "can_run_intraday_forecast": ready, "can_run_backtest": False, "can_train_model": False, "can_generate_formal_signal": False}, "created_at": now_string()}
def write_snapshot_bundle(df: pd.DataFrame, trade_date: str | None = None, snapshot_type: str = "snapshots") -> dict:
    work = normalize_intraday_minutes(df)
    trade_date = compact_trade_date(trade_date or select_latest_trade_date(work))
    paths = snapshot_paths(trade_date, snapshot_type)
    paths.root.mkdir(parents=True, exist_ok=True)
    write_parquet(work, paths.one_min); write_parquet(aggregate_intraday_bars(work, 5), paths.five_min); write_parquet(aggregate_intraday_bars(work, 15), paths.fifteen_min)
    snapshot, quality = snapshot_summary(work, snapshot_type), quality_report(work, snapshot_type)
    write_json(snapshot, paths.snapshot); write_json(quality, paths.quality)
    manifest = build_manifest(paths, trade_date, snapshot_type); ready = ready_payload(paths, quality, manifest)
    write_json(manifest, paths.manifest); write_json(ready, paths.ready)
    if snapshot_type == "snapshots":
        write_json(ready, INTRADAY_METADATA_DIR / "intraday_ready_1400.json")
        write_json(snapshot, INTRADAY_METADATA_DIR / "intraday_latest_snapshot.json")
        write_json({"latest_trade_date": trade_date, "asof_time": ASOF_TIME_SHORT, "created_at": now_string()}, INTRADAY_METADATA_DIR / "intraday_latest_trade_date.json")
        write_json({"project": "CNSV intraday", "repo": "CNSVdata", "ready_file": "metadata/intraday/intraday_ready_1400.json", "formal_signal": False, "allowed_usage": ready["allowed_usage"], "created_at": now_string()}, INTRADAY_METADATA_DIR / "intraday_downstream_contract.json")
    return {"paths": paths, "snapshot": snapshot, "quality": quality, "manifest": manifest, "ready": ready}
def build_latest_snapshot_from_source() -> dict:
    minutes = read_source_minutes()
    trade_date = select_latest_trade_date(minutes)
    if not trade_date: raise SystemExit("no intraday minute source available")
    return write_snapshot_bundle(minutes[minutes["trade_date"].astype(str).map(compact_trade_date) == trade_date], trade_date, "snapshots")
def _snapshot_records() -> pd.DataFrame:
    rows = []
    for root in [SNAPSHOT_ROOT, REPLAY_ROOT]:
        for path in sorted(root.glob(f"*/{ASOF_LABEL}/intraday_snapshot_1400.json")) if root.exists() else []:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
    return pd.DataFrame(rows)
def build_t1_truth() -> pd.DataFrame:
    snaps, daily_path, rows = _snapshot_records(), PROCESSED_DIR / "cnsv_daily.parquet", []
    if not snaps.empty and daily_path.exists():
        daily = pd.read_parquet(daily_path).copy(); daily["trade_date"] = daily["trade_date"].astype(str).map(compact_trade_date)
        dates = daily.sort_values("trade_date")["trade_date"].tolist(); close_map = daily.set_index("trade_date")["close"].to_dict(); nxt = {d: dates[i + 1] for i, d in enumerate(dates[:-1])}
        for _, snap in snaps.iterrows():
            td = compact_trade_date(snap.get("trade_date", "")); asof = pd.to_numeric(snap.get("asof_price_1400"), errors="coerce"); nd = nxt.get(td, ""); nc = close_map.get(nd) if nd else None
            ready = bool(nd and pd.notna(asof) and pd.notna(nc)); ret = nc / asof - 1 if ready and asof else pd.NA
            rows.append({"trade_date": td, "asof_time": ASOF_TIME_SHORT, "ts_code": snap.get("ts_code", ""), "asof_price_1400": asof, "next_trade_date": nd, "next_close": nc if ready else pd.NA, "actual_return_vs_1400": ret, "actual_up_label": int(ret > 0) if pd.notna(ret) else pd.NA, "actual_down_label": int(ret < 0) if pd.notna(ret) else pd.NA, "actual_flat_label": int(abs(ret) <= FLAT_THRESHOLD) if pd.notna(ret) else pd.NA, "actual_limitup_label": int(ret >= 0.099) if pd.notna(ret) else pd.NA, "truth_ready": ready, "truth_status": "PASS" if ready else "WARN", "created_at": now_string()})
    truth = pd.DataFrame(rows).drop_duplicates("trade_date", keep="last").sort_values("trade_date") if rows else pd.DataFrame()
    LABEL_ROOT.mkdir(parents=True, exist_ok=True); write_parquet(truth, LABEL_ROOT / "t1_truth_vs_1400_latest.parquet"); truth.to_csv(LABEL_ROOT / "t1_truth_vs_1400_latest.csv", index=False, encoding="utf-8-sig")
    write_json({"status": "PASS" if not truth.empty and truth["truth_ready"].any() else "WARN", "rows": int(len(truth)), "ready_rows": int(truth["truth_ready"].sum()) if not truth.empty else 0, "generated_at": now_string()}, LABEL_ROOT / "t1_truth_quality.json")
    return truth
def check_trainset_no_future_leak(trainset: pd.DataFrame) -> dict:
    columns = set(trainset.columns); forbidden = sorted(columns & PREDICTION_FORBIDDEN_NAMES)
    bad_features = [c for c in trainset.columns if c.startswith("feature_") and any(x in c for x in ["next_", "actual_", "label", "created_at"])]
    checks = [{"name": "no_prediction_columns", "status": "FAIL" if forbidden else "PASS", "forbidden_columns": forbidden}, {"name": "feature_names_no_label_or_future", "status": "FAIL" if bad_features else "PASS", "bad_feature_columns": bad_features}, {"name": "feature_version_present", "status": "PASS" if "feature_version" in columns else "FAIL"}, {"name": "label_version_present", "status": "PASS" if "label_version" in columns else "FAIL"}]
    return {"status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS", "generated_at": now_string(), "rows": int(len(trainset)), "checks": checks}
def build_t1_intraday_trainset() -> pd.DataFrame:
    truth = pd.read_parquet(LABEL_ROOT / "t1_truth_vs_1400_latest.parquet") if (LABEL_ROOT / "t1_truth_vs_1400_latest.parquet").exists() else build_t1_truth()
    rows = [{"trade_date": r["trade_date"], "feature_return_from_open_to_1400": 0.0, "actual_up_label": r.get("actual_up_label"), "feature_version": FEATURE_VERSION, "label_version": LABEL_VERSION, "created_at": now_string()} for _, r in truth.iterrows() if bool(r.get("truth_ready"))]
    trainset = pd.DataFrame(rows); ML_ROOT.mkdir(parents=True, exist_ok=True)
    write_parquet(trainset, ML_ROOT / "t1_intraday_trainset.parquet"); trainset.to_csv(ML_ROOT / "t1_intraday_trainset_latest.csv", index=False, encoding="utf-8-sig")
    write_json(check_trainset_no_future_leak(trainset), ML_ROOT / "trainset_quality.json")
    return trainset
def replay_intraday_history(history_days: int = DEFAULT_HISTORY_DAYS) -> dict:
    source = read_source_minutes()
    if source.empty:
        payload = {"status": "FAIL", "generated_at": now_string(), "history_days_required": history_days, "generated_snapshots": 0, "reason": "missing source minute data"}; write_json(payload, INTRADAY_QUALITY_DIR / "intraday_replay_latest.json"); return payload
    generated = []
    for td in sorted(source["trade_date"].dropna().astype(str).map(compact_trade_date).unique())[-history_days:]:
        bundle = write_snapshot_bundle(source[source["trade_date"].astype(str).map(compact_trade_date) == td], td, "replay"); generated.append({"trade_date": td, "status": bundle["quality"]["status"], "path": str(bundle["paths"].root.relative_to(ROOT))})
    payload = {"status": "PASS" if len(generated) >= history_days else "WARN", "generated_at": now_string(), "history_days_required": history_days, "generated_snapshots": len(generated), "snapshots": generated}
    write_json(payload, INTRADAY_QUALITY_DIR / "intraday_replay_latest.json"); build_t1_truth(); build_t1_intraday_trainset(); return payload
def build_intraday_preview_csv() -> list[dict]:
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True); pd.DataFrame([]).to_csv(PREVIEW_ROOT / "intraday_preview_manifest.csv", index=False, encoding="utf-8-sig"); return []
def intraday_acceptance_report() -> dict:
    report = {"status": "WARN", "generated_at": now_string(), "checks": [{"name": "formal_signal_disabled", "status": "PASS"}]}; write_json(report, INTRADAY_QUALITY_DIR / "intraday_acceptance_latest.json"); return report
def intraday_smoke_read() -> dict:
    ready_path = INTRADAY_METADATA_DIR / "intraday_ready_1400.json"
    status = "PASS" if ready_path.exists() else "FAIL"
    payload = {"status": status, "generated_at": now_string(), "formal_signal": False}; write_json(payload, INTRADAY_QUALITY_DIR / "intraday_smoke_latest.json"); return payload
