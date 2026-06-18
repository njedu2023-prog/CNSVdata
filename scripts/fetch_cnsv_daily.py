from cnsvdata.common import load_yaml, normalize_trade_date, now_string, write_parquet
from cnsvdata.paths import PROCESSED_DIR, RAW_DIR
from cnsvdata.tushare_client import call_with_retry, get_tushare_pro


def main() -> None:
    target = load_yaml("target.yml")["target"]
    pro = get_tushare_pro()
    df = call_with_retry(
        pro.daily,
        ts_code=target["ts_code"],
        start_date="20100101",
        fields="ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount",
    )
    df["trade_date"] = df["trade_date"].map(normalize_trade_date)
    df["source"] = "tushare"
    df["fetched_at"] = now_string()
    df = df.sort_values("trade_date")
    write_parquet(df, RAW_DIR / "cnsv_daily_raw.parquet")
    write_parquet(df, PROCESSED_DIR / "cnsv_daily.parquet")


if __name__ == "__main__":
    main()
