import os

from cnsvdata.common import load_yaml, merge_existing_parquet, normalize_trade_date, now_string, write_parquet
from cnsvdata.paths import PROCESSED_DIR, RAW_DIR
from cnsvdata.tushare_client import call_with_retry, get_tushare_pro
from cnsvdata.validators import derive_moneyflow_net_amount


def main() -> None:
    target = load_yaml("target.yml")["target"]
    pro = get_tushare_pro()
    start_date = os.getenv("CNSVDATA_BACKFILL_START_DATE", "20100101")
    end_date = os.getenv("CNSVDATA_BACKFILL_END_DATE", "")
    kwargs = {"ts_code": target["ts_code"], "start_date": start_date}
    if end_date:
        kwargs["end_date"] = end_date
    df = call_with_retry(pro.moneyflow, **kwargs)
    df["trade_date"] = df["trade_date"].map(normalize_trade_date)
    df["source"] = "tushare"
    df["source_version"] = "tushare.moneyflow"
    df["field_definition"] = "Amounts are inferred by vendor order-size classification; net_mf_amount is source value or derived from buy/sell amount components when source net is null."
    df["fetched_at"] = now_string()
    keep = [
        "ts_code", "trade_date", "buy_sm_amount", "sell_sm_amount", "buy_md_amount", "sell_md_amount",
        "buy_lg_amount", "sell_lg_amount", "buy_elg_amount", "sell_elg_amount", "net_mf_amount",
        "source", "source_version", "field_definition", "fetched_at",
    ]
    df = df[keep].sort_values("trade_date")
    df, _ = derive_moneyflow_net_amount(df)
    df = merge_existing_parquet(df, PROCESSED_DIR / "cnsv_moneyflow.parquet", ["trade_date"], "trade_date")
    write_parquet(df, RAW_DIR / "cnsv_moneyflow_raw.parquet")
    write_parquet(df, PROCESSED_DIR / "cnsv_moneyflow.parquet")


if __name__ == "__main__":
    main()
