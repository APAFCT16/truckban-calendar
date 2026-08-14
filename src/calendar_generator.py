from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import json
import re
import hashlib


COUNTRIES_FILE = Path("countries.json")
OUTPUT_FILE = Path("public/truckban.ics")

BASE_URL = "https://truckban.eu/"

DAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


class TextExtractor(HTMLParser):
    """Convert TruckBAN HTML into reasonably clean text."""

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        text = " ".join(data.split())
        if text:
            self.parts.append(text)

    def get_text(self):
        return "\n".join(self.parts)


def load_countries():
    with COUNTRIES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)["countries"]


def country_url(country):
    return BASE_URL + country.replace(" ", "%20")


def download_page(url):
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0 Safari/537.36"
            )
        },
    )

    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def html_to_text(html):
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text()


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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


def event_uid(country, date, title):
    raw = f"{country}|{date}|{title}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{digest}@truckban-calendar"


def make_event(
    country,
    start,
    end,
    title,
    description,
):
    uid = event_uid(country, start.date().isoformat(), title)

    return "\r\n".join(
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

    lines.extend(events)
    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"


def make_weekly_events(country, text, start_date, end_date):
    """
    Conservative first-pass parser.

    This intentionally only recognises very clear recurring
    Sunday/Saturday restrictions. More complicated seasonal,
    holiday and route-specific rules will be added separately.
    """

    events = []

    lower = text.lower()

    # Explicitly skip countries where TruckBAN says there is
    # no general Sunday/public-holiday ban.
    no_general_ban = (
        "no general driving ban on sundays and public holidays"
        in lower
    )

    if no_general_ban:
        print(f"{country}: no general Sunday/public-holiday ban")
        return events

    # ---- Sunday 00:00-22:00 ----
    if (
        "sundays and public holidays from 00:00 to 22"
        in lower
        or "sundays and public holidays between 00:00 and 22"
        in lower
        or "sundays and public holidays between 0:00 and 22"
        in lower
    ):
        current = start_date

        while current <= end_date:
            if current.weekday() == DAYS["Sunday"]:
                start = datetime(
                    current.year,
                    current.month,
                    current.day,
                    0,
                    0,
                    tzinfo=timezone.utc,
                )
                finish = start + timedelta(hours=22)

                title = f"🚛 {country} – HGV Driving Ban"

                description = (
                    "Recurring Sunday HGV driving restriction.\n\n"
                    f"TruckBAN information:\n{text[:2500]}\n\n"
                    f"Source: {country_url(country)}"
                )

                events.append(
                    make_event(
                        country,
                        start,
                        finish,
                        title,
                        description,
                    )
                )

            current += timedelta(days=1)

    return events


def main():
    countries = load_countries()

    print(f"Loaded {len(countries)} countries.")

    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=90)

    events = []
    successful = 0
    failed = 0

    for country in countries:
        print(f"\nChecking {country}...")

        url = country_url(country)

        try:
            html = download_page(url)
            text = clean_text(html_to_text(html))

            if not text:
                raise RuntimeError("TruckBAN page contained no readable text")

            successful += 1

            print(
                f"{country}: downloaded {len(html):,} characters"
            )

            events.extend(
                make_weekly_events(
                    country,
                    text,
                    today,
                    end_date,
                )
            )

        except Exception as error:
            failed += 1
            print(
                f"{country}: FAILED - "
                f"{type(error).__name__}: {error}"
            )

    print("\n------------------------------")
    print(f"Successful countries: {successful}")
    print(f"Failed countries:     {failed}")
    print(f"Calendar events:      {len(events)}")
    print("------------------------------")

    # Fail safely if TruckBAN is unavailable.
    if successful == 0:
        raise RuntimeError(
            "TruckBAN could not be accessed for any country. "
            "Existing calendar has NOT been replaced."
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    calendar = build_calendar(events)

    OUTPUT_FILE.write_text(
        calendar,
        encoding="utf-8",
    )

    print(f"\nCalendar written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
