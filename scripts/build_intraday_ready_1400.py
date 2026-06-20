from cnsvdata.intraday import build_latest_snapshot_from_source, build_missing_source_ready


def main() -> None:
    try:
        build_latest_snapshot_from_source()
    except SystemExit:
        build_missing_source_ready()


if __name__ == "__main__":
    main()
