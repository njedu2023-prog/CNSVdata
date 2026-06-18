from cnsvdata.common import load_yaml, normalize_trade_date, now_string, write_json, write_parquet
from cnsvdata.paths import METADATA_DIR, PROCESSED_DIR, RAW_DIR
from cnsvdata.tushare_client import call_with_retry, get_tushare_pro


def main() -> None:
    config = load_yaml("calendar.yml")["calendar"]
    pro = get_tushare_pro()
    raw = call_with_retry(
        pro.trade_cal,
        exchange=config["exchange"],
        start_date="20100101",
        end_date="20301231",
        fields="exchange,cal_date,is_open,pretrade_date",
    )
    raw["cal_date"] = raw["cal_date"].map(normalize_trade_date)
    raw["pretrade_date"] = raw["pretrade_date"].fillna("").map(normalize_trade_date)
    raw["exchange"] = config["exchange"]
    raw = raw[["cal_date", "is_open", "pretrade_date", "exchange"]].sort_values("cal_date")

    write_parquet(raw, RAW_DIR / "trade_calendar_raw.parquet")
    write_parquet(raw, PROCESSED_DIR / "trade_calendar.parquet")

    open_days = raw.loc[raw["is_open"] == 1, "cal_date"].tolist()
    today = now_string()[:10]
    latest = max(day for day in open_days if day <= today)
    next_trade = min(day for day in open_days if day > today)
    generated_at = now_string()

    write_json(
        {
            "latest_trade_date": latest,
            "source": "tushare",
            "generated_at": generated_at,
            "timezone": config["timezone"],
        },
        METADATA_DIR / "latest_trade_date.json",
    )
    write_json(
        {
            "current_trade_date": latest,
            "next_trade_date": next_trade,
            "source": "tushare",
            "generated_at": generated_at,
            "timezone": config["timezone"],
        },
        METADATA_DIR / "next_trade_date.json",
    )


if __name__ == "__main__":
    main()
