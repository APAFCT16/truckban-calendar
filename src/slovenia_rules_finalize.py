from pathlib import Path
import re

GEN = Path("src/calendar_generator.py")

SLOVENIA_BRANCH = '''        elif country == "Slovenia":
            named_holiday = holiday_name(country, d) if h else None
            if d.weekday() == 6:
                if named_holiday:
                    add(E,country,f"HGV ban — {named_holiday}",d,"08:00","22:00",f">7.5t on affected road sections; {named_holiday} public-holiday restriction. Statutory exemptions apply.")
                else:
                    add(E,country,"HGV ban — Sunday",d,"08:00","22:00",">7.5t on affected road sections; Sunday restriction. Statutory exemptions apply.")
            elif h:
                label = named_holiday or "public holiday"
                add(E,country,f"HGV ban — {label}",d,"08:00","22:00",f">7.5t on affected road sections; {label} public-holiday restriction. Statutory exemptions apply.")

            year = d.year
            a = year % 19
            b = year // 100
            c = year % 100
            ee = b // 4
            f = b % 4
            g = (b + 8) // 25
            hh = (b - g + 1) // 3
            i = (19 * a + b - ee - hh + 15) % 30
            k = c // 4
            l = (32 + 2 * f + 2 * k - i - (c % 4)) % 7
            m = (a + 11 * i + 22 * l) // 451
            easter_month = (i + l - 7 * m + 114) // 31
            easter_day = ((i + l - 7 * m + 114) % 31) + 1
            easter = date(year, easter_month, easter_day)
            if d == easter - timedelta(days=2):
                add(E,country,"HGV ban — Good Friday",d,"14:00","22:00",">7.5t on affected road sections; Good Friday special restriction. Statutory exemptions apply.")

            summer_start = last_weekday(d.year,6,5)
            first_sunday_september = 1 + ((6 - date(d.year,9,1).weekday()) % 7)
            summer_end = date(d.year,9,first_sunday_september)
            if summer_start <= d <= summer_end and d.weekday() == 5:
                add(E,country,"HGV ban — summer Saturday",d,"08:00","13:00",">7.5t on affected road sections; tourist-season Saturday restriction.")
                add(E,country,"HGV ban — summer Saturday — listed routes",d,"06:00","16:00",">7.5t on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača-Fernetiči, H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane; tourist-season route-specific restriction.")
'''


def replace_branch(text):
    pattern = re.compile(r'(?ms)^        elif country == "Slovenia":\n.*?(?=^        elif country == "Switzerland":)')
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one Slovenia branch before Switzerland (matches={len(matches)})")
    return text[:matches[0].start()] + SLOVENIA_BRANCH + text[matches[0].end():]


def main():
    text = replace_branch(GEN.read_text(encoding="utf-8"))
    GEN.write_text(text, encoding="utf-8")

    # Prove the generated rule can actually produce the next applicable 2026
    # Saturday before the calendar is built. This is a data guard, not a
    # suppression of the downstream feed validator.
    import sys
    sys.path.insert(0, str(GEN.parent))
    from calendar_generator import country_events
    from datetime import date

    events = country_events("Slovenia", date(2026, 9, 4), date(2026, 9, 5))
    summaries = {(a.date(), title, a.astimezone(__import__('zoneinfo').ZoneInfo('Europe/Ljubljana')).strftime('%H:%M'), b.astimezone(__import__('zoneinfo').ZoneInfo('Europe/Ljubljana')).strftime('%H:%M')) for a, b, _, title, _ in events}
    expected = {
        (date(2026, 9, 5), "HGV ban — summer Saturday", "08:00", "13:00"),
        (date(2026, 9, 5), "HGV ban — summer Saturday — listed routes", "06:00", "16:00"),
    }
    if not expected.issubset(summaries):
        raise SystemExit(f"Slovenia final rule guard failed; expected {expected}, got {sorted(summaries)}")
    print("Slovenia final rule guard passed: 5 September 2026 general and listed-route Saturday events are generated.")


if __name__ == "__main__":
    main()
