from cnsvdata.intraday import intraday_smoke_read


def main() -> None:
    report = intraday_smoke_read()
    if report["status"] == "FAIL":
        print("intraday smoke status is FAIL")


if __name__ == "__main__":
    main()
