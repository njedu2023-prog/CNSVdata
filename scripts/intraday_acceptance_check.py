from cnsvdata.intraday import intraday_acceptance_report


def main() -> None:
    report = intraday_acceptance_report()
    if report["status"] == "FAIL":
        print("intraday acceptance status is FAIL")


if __name__ == "__main__":
    main()
