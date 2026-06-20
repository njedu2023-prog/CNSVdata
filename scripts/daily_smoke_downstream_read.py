from cnsvdata.daily import daily_smoke_read


def main() -> None:
    report = daily_smoke_read()
    if report["status"] == "FAIL":
        raise SystemExit("daily smoke status is FAIL")


if __name__ == "__main__":
    main()
