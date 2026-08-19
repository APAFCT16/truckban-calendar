from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ICS = Path("public/countries/Poland.ics")
WARSAW = ZoneInfo("Europe/Warsaw")
UTC = ZoneInfo("UTC")


def events():
    if not ICS.is_file() or ICS.stat().st_size == 0:
        raise SystemExit("Poland.ics is missing or empty")
    text = ICS.read_text(encoding="utf-8")
    if "BEGIN:VCALENDAR" not in text or "END:VCALENDAR" not in text:
        raise SystemExit("Poland.ics is not a complete VCALENDAR")
    if "X-WR-CALNAME:TruckBAN — Poland" not in text:
        raise SystemExit("Poland calendar name is missing")
    if "DTSTART;TZID=" in text or "DTEND;TZID=" in text:
        raise SystemExit("Poland.ics contains TZID-based timestamps; Classic Outlook requires UTC publication")

    out = []
    current = None
    for line in text.splitlines():
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            if current is not None:
                out.append(current)
            current = None
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            if key in {"SUMMARY", "DTSTART", "DTEND", "DESCRIPTION"}:
                current[key] = value
    return out


def utc_to_local(value):
    return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC).astimezone(WARSAW)


def find(events_list, summary, local_date, start_hour, end_hour):
    for e in events_list:
        if e.get("SUMMARY") != summary:
            continue
        start = utc_to_local(e["DTSTART"])
        end = utc_to_local(e["DTEND"])
        if start.date() == local_date and start.hour == start_hour and end.date() == local_date and end.hour == end_hour:
            return e
    raise SystemExit(f"Missing Poland event: {summary} {local_date} {start_hour:02d}:00-{end_hour:02d}:00 local")


if __name__ == "__main__":
    from datetime import date

    E = events()

    # Future summer dates in the generated window. Warsaw is UTC+2 in August.
    find(E, "Poland — HGV ban — summer Friday", date(2026, 8, 21), 18, 22)
    find(E, "Poland — HGV ban — summer Saturday", date(2026, 8, 22), 8, 14)
    find(E, "Poland — HGV ban — summer Sunday", date(2026, 8, 23), 8, 22)

    # Holiday eve and holiday across the October/November DST boundary.
    find(E, "Poland — HGV ban — public holiday eve", date(2026, 11, 10), 18, 22)
    find(E, "Poland — HGV ban — public holiday", date(2026, 11, 11), 8, 22)

    # 6 January is a Polish public holiday but is NOT a §2 traffic-ban holiday.
    for e in E:
        if e.get("SUMMARY") == "Poland — HGV ban — public holiday":
            if utc_to_local(e["DTSTART"]).date() == date(2027, 1, 6):
                raise SystemExit("Poland feed incorrectly contains an HGV public-holiday ban on 6 January")

    # 2027 movable holidays: Pentecost and Corpus Christi, including their eves.
    # In 2027 Easter Sunday is 28 March, Pentecost is 16 May and Corpus Christi
    # is 27 May. The previous validation incorrectly used 3 June for Corpus Christi.
    find(E, "Poland — HGV ban — public holiday eve", date(2027, 5, 15), 18, 22)
    find(E, "Poland — HGV ban — public holiday", date(2027, 5, 16), 8, 22)
    find(E, "Poland — HGV ban — public holiday eve", date(2027, 5, 26), 18, 22)
    find(E, "Poland — HGV ban — public holiday", date(2027, 5, 27), 8, 22)

    # Summer 2027 must continue through the final Sunday of August.
    find(E, "Poland — HGV ban — summer Friday", date(2027, 8, 27), 18, 22)
    find(E, "Poland — HGV ban — summer Saturday", date(2027, 8, 28), 8, 14)
    find(E, "Poland — HGV ban — summer Sunday", date(2027, 8, 29), 8, 22)

    # Scope text must state the statutory >12t threshold and exemptions.
    if not any(">12t permissible maximum mass" in e.get("DESCRIPTION", "") for e in E):
        raise SystemExit("Poland event descriptions do not state the >12t statutory scope")
    if not any("statutory exemptions" in e.get("DESCRIPTION", "") for e in E):
        raise SystemExit("Poland event descriptions do not state statutory exemptions")

    print(f"Poland feed validation passed: {len(E)} events inspected")
