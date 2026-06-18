import pandas as pd

from cnsvdata.common import load_yaml, now_string, write_parquet
from cnsvdata.paths import PROCESSED_DIR


def main() -> None:
    ts_code = load_yaml("target.yml")["target"]["ts_code"]
    created_at = now_string()
    df = pd.DataFrame(
        [
            {
                "ts_code": ts_code,
                "event_date": "2025-09-01",
                "available_at": "2025-09-01",
                "event_type": "merger",
                "event_name": "中国船舶吸收合并中国重工",
                "description": "重大资产重组相关结构事件，具体生效日期需随公告复核。",
                "raw_source": "manual_seed",
                "impact_level": "high",
                "created_at": created_at,
            }
        ]
    )
    write_parquet(df, PROCESSED_DIR / "corporate_actions.parquet")


if __name__ == "__main__":
    main()
