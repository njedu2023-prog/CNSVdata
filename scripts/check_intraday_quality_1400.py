from cnsvdata.intraday import build_latest_snapshot_from_source


def main() -> None:
    bundle = build_latest_snapshot_from_source()
    if bundle["quality"]["status"] == "FAIL":
        raise SystemExit("intraday quality status is FAIL")


if __name__ == "__main__":
    main()
