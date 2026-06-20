import os

from cnsvdata.intraday import DEFAULT_HISTORY_DAYS, replay_intraday_history


def main() -> None:
    history_days = int(os.getenv("CNSVDATA_INTRADAY_HISTORY_DAYS", str(DEFAULT_HISTORY_DAYS)))
    replay_intraday_history(history_days=history_days)


if __name__ == "__main__":
    main()
