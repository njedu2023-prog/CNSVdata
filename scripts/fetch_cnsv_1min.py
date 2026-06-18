from cnsvdata.common import load_yaml, now_string, write_parquet
from cnsvdata.paths import PROCESSED_DIR, RAW_DIR
from cnsvdata.tushare_client import call_with_retry, get_tushare_pro


def main() -> None:
    target = load_yaml("target.yml")["target"]
    config = load_yaml("tushare.yml")["tushare"]
    pro = get_tushare_pro()
    df = call_with_retry(
        pro.stk_mins,
        ts_code=target["ts_code"],
        freq=config["minute_freq"],
    )
    if "trade_time" not in df.columns and "trade_date" in df.columns:
        df = df.rename(columns={"trade_date": "trade_time"})
    df["trade_time"] = df["trade_time"].astype(str)
    dt = df["trade_time"].str.slice(0, 19)
    df["trade_date"] = dt.str.slice(0, 10)
    df["time"] = dt.str.slice(11, 19)
    df["source"] = "tushare"
    df["fetched_at"] = now_string()
    keep = ["ts_code", "trade_time", "trade_date", "time", "open", "high", "low", "close", "vol", "amount", "source", "fetched_at"]
    df = df[keep].drop_duplicates(subset=["trade_time"]).sort_values("trade_time")
    write_parquet(df, RAW_DIR / "cnsv_1min_raw.parquet")
    write_parquet(df, PROCESSED_DIR / "cnsv_1min.parquet")


if __name__ == "__main__":
    main()
