from pathlib import Path


PUBLIC_DIR = Path("public")
TARGET_SUMMARY = "SUMMARY:Poland — HGV ban — summer Sunday"
TARGET_START = "DTSTART:20270815T060000Z"
TARGET_END = "DTEND:20270815T200000Z"


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

        # Match the complete VEVENT rather than relying on a particular line
        # order. This also survives any harmless generator reordering.
        summary = next((x for x in event if x == TARGET_SUMMARY), "")
        dtstart = next((x for x in event if x == TARGET_START), "")
        dtend = next((x for x in event if x == TARGET_END), "")

        if summary and dtstart and dtend:
            removed += 1
            return

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

    # A malformed trailing event should never silently disappear.
    if event:
        out.extend(event)

    path.write_text("\r\n".join(out) + "\r\n", encoding="utf-8")
    return removed


def main():
    paths = [PUBLIC_DIR / "countries" / "Poland.ics", PUBLIC_DIR / "truckban.ics"]
    total = 0
    for path in paths:
        if path.exists():
            removed = clean_ics(path)
            print(f"{path}: removed {removed} redundant Poland 15 August 2027 summer-Sunday event(s).")
            total += removed

    if total == 0:
        print("No redundant Poland 15 August 2027 summer-Sunday event found.")
    else:
        print(f"Removed {total} redundant Poland 15 August 2027 summer-Sunday event(s) in total.")


if __name__ == "__main__":
    main()
