import pandas as pd

from cnsvdata.common import write_json, write_parquet
from cnsvdata.paths import PROCESSED_DIR, QUALITY_DIR


def aggregate_minutes(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    work = df.copy()
    work["trade_time"] = pd.to_datetime(work["trade_time"])
    grouped = (
        work.set_index("trade_time")
        .groupby("ts_code")
        .resample(freq, closed="left", label="right")
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            vol=("vol", "sum"),
            amount=("amount", "sum"),
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    grouped["trade_time"] = grouped["trade_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    grouped["trade_date"] = grouped["trade_time"].str.slice(0, 10)
    grouped["time"] = grouped["trade_time"].str.slice(11, 19)
    grouped["source"] = "derived_from_1min"
    grouped["fetched_at"] = work["fetched_at"].max() if "fetched_at" in work.columns else ""
    return grouped[["ts_code", "trade_time", "trade_date", "time", "open", "high", "low", "close", "vol", "amount", "source", "fetched_at"]]


def main() -> None:
    one_min_path = PROCESSED_DIR / "cnsv_1min.parquet"
    if not one_min_path.exists():
        raise FileNotFoundError(one_min_path)
    one_min = pd.read_parquet(one_min_path)
    report = {"status": "PASS", "checks": []}
    for label, freq in {"5min": "5min", "15min": "15min", "30min": "30min", "60min": "60min"}.items():
        out = aggregate_minutes(one_min, freq)
        write_parquet(out, PROCESSED_DIR / f"cnsv_{label}.parquet")
        report["checks"].append(
            {
                "freq": label,
                "rows": int(len(out)),
                "source_rows": int(len(one_min)),
                "source": "cnsv_1min.parquet",
            }
        )
    write_json(report, QUALITY_DIR / "minute_aggregation_check.json")


if __name__ == "__main__":
    main()
