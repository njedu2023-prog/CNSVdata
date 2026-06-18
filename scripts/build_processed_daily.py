from cnsvdata.paths import PROCESSED_DIR, RAW_DIR
from cnsvdata.common import write_parquet

import pandas as pd


def main() -> None:
    raw_path = RAW_DIR / "cnsv_daily_raw.parquet"
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    df = pd.read_parquet(raw_path).drop_duplicates(subset=["trade_date"]).sort_values("trade_date")
    write_parquet(df, PROCESSED_DIR / "cnsv_daily.parquet")


if __name__ == "__main__":
    main()
