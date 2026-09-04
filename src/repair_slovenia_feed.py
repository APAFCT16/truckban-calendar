from datetime import date, datetime, timezone
from pathlib import Path

PUBLIC = Path("public/countries/Slovenia.ics")


def main():
    # country_feeds applies additional generator patches in its own process.
    # Rebuild Slovenia's published country feed from the canonical generator
    # state after that process has completed, so the country feed cannot silently
    # diverge from the combined calendar.
    from calendar_generator import load_countries, country_events, make_ics

    countries = load_countries()
    if "Slovenia" not in countries:
        raise SystemExit("Slovenia is missing from countries.json")

    today = datetime.now(timezone.utc).date()
    stop = date(today.year + 1, 12, 31)
    events = country_events("Slovenia", today, stop)
    ics = make_ics(events).replace(
        "X-WR-CALNAME:TruckBAN HGV Restrictions",
        "X-WR-CALNAME:TruckBAN — Slovenia",
        1,
    )

    lines = ics.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("X-WR-CALDESC:"):
            lines[i] = (
                "X-WR-CALDESC:Slovenia: HGVs over 7.5t are restricted Sundays and public holidays 08:00-22:00, "
                "with Good Friday 14:00-22:00. During the tourist season (last Saturday of June through "
                "first Sunday of September), Saturdays are restricted 08:00-13:00 generally, with "
                "06:00-16:00 on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača-Fernetiči, "
                "H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane. "
                "Statutory exemptions and route-specific rules apply; this feed represents the recurring national framework only."
            )
            break
    else:
        raise SystemExit("Missing X-WR-CALDESC in rebuilt Slovenia feed")

    PUBLIC.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")

    required = (
        "SUMMARY:Slovenia — HGV ban — summer Saturday",
        "DTSTART:20260905T060000Z",
        "DTEND:20260905T110000Z",
        "SUMMARY:Slovenia — HGV ban — summer Saturday — listed routes",
        "DTSTART:20260905T040000Z",
        "DTEND:20260905T140000Z",
    )
    text = PUBLIC.read_text(encoding="utf-8")
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise SystemExit(f"Rebuilt Slovenia feed is missing required 5 September 2026 data: {missing}")
    print("Rebuilt Slovenia country feed from canonical generator events; 5 September 2026 general and listed-route restrictions are present.")


if __name__ == "__main__":
    main()
