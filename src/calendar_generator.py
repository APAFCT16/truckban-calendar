from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json


COUNTRIES_FILE = Path("countries.json")
OUTPUT_FILE = Path("public/truckban.ics")


def load_countries():
    with COUNTRIES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data["countries"]


def event_uid(country, date, title):
    raw = f"{country}|{date}|{title}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"{digest}@truckban-calendar"


def escape_ics(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def format_dt(dt):
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_event(
    country,
    start,
    end,
    title,
    description="",
):
    uid = event_uid(country, start.date().isoformat(), title)

    return "\n".join(
        [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{format_dt(datetime.now(timezone.utc))}",
            f"DTSTART:{format_dt(start)}",
            f"DTEND:{format_dt(end)}",
            f"SUMMARY:{escape_ics(title)}",
            f"DESCRIPTION:{escape_ics(description)}",
            "END:VEVENT",
        ]
    )


def build_calendar(events):
    now = datetime.now(timezone.utc)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TruckBAN Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:TruckBAN - European HGV Restrictions",
        "X-WR-CALDESC:European HGV driving restrictions from TruckBAN",
        "X-WR-TIMEZONE:Europe/London",
    ]

    for event in events:
        lines.append(event)

    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"


def main():
    countries = load_countries()

    print(f"Loaded {len(countries)} countries:")
    for country in countries:
        print(f" - {country}")

    # Temporary test event.
    # This will be replaced with actual TruckBAN data
    # in the next stage.
    start = datetime.now(timezone.utc) + timedelta(days=7)
    end = start + timedelta(hours=2)

    description = (
        "TEST EVENT - this will be replaced by actual TruckBAN "
        "driving restriction data.\n\n"
        "Source: https://truckban.eu/"
    )

    events = [
        create_event(
            "TEST",
            start,
            end,
            "🚛 TruckBAN Calendar – Test Event",
            description,
        )
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(build_calendar(events), encoding="utf-8")

    print(f"\nCalendar written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
