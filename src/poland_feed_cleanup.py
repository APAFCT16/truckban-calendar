from pathlib import Path


TARGET = "Poland"
PUBLIC_DIR = Path("public")


def clean_ics(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    out = []
    event = []
    removed = 0

    def flush():
        nonlocal removed
        if not event:
            return
        summary = next((x for x in event if x.startswith("SUMMARY:")), "")
        dtstart = next((x for x in event if x.startswith("DTSTART:")), "")
        dtend = next((x for x in event if x.startswith("DTEND:")), "")
        duplicate = (
            summary == "SUMMARY:Poland — HGV ban — summer Sunday"
            and dtstart == "DTSTART:20270815T060000Z"
            and dtend == "DTEND:20270815T200000Z"
        )
        if duplicate:
            removed += 1
        else:
            out.extend(event)

    for line in lines:
        if line == "BEGIN:VEVENT":
            event = [line]
        elif event:
            event.append(line)
            if line == "END:VEVENT":
                flush()
                event = []
        else:
            out.append(line)

    flush()
    path.write_text("\r\n".join(out) + "\r\n", encoding="utf-8")
    return removed


def main():
    paths = [PUBLIC_DIR / "countries" / "Poland.ics", PUBLIC_DIR / "truckban.ics"]
    total = 0
    for path in paths:
        if path.exists():
            total += clean_ics(path)
    if total:
        print(f"Removed {total} redundant Poland summer-Sunday event(s) for 15 August 2027.")
    else:
        print("No redundant Poland 15 August 2027 summer-Sunday event found.")


if __name__ == "__main__":
    main()
