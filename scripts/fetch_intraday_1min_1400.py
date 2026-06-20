import os

from cnsvdata.intraday import DEFAULT_HISTORY_DAYS, fetch_intraday_from_tushare, write_latest_intraday_minutes


def main() -> None:
    history_days = int(os.getenv("CNSVDATA_INTRADAY_HISTORY_DAYS", str(DEFAULT_HISTORY_DAYS)))
    df = fetch_intraday_from_tushare(history_days=history_days)
    write_latest_intraday_minutes(df)


if __name__ == "__main__":
    main()
