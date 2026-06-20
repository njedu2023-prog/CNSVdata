from cnsvdata.daily import daily_acceptance_report


def main() -> None:
    report = daily_acceptance_report()
    if report["status"] == "FAIL":
        raise SystemExit("daily acceptance status is FAIL")


if __name__ == "__main__":
    main()
