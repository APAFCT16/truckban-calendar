# Verified Belgium, Luxembourg, Slovakia and Hungary country-specific rules.
from pathlib import Path
import re

GEN = Path("src/calendar_generator.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

    old_tz = '"Austria": "Europe/Vienna", "Croatia": "Europe/Zagreb", "Czech Republic": "Europe/Prague",'
    new_tz = '"Austria": "Europe/Vienna", "Belgium": "Europe/Brussels", "Croatia": "Europe/Zagreb", "Czech Republic": "Europe/Prague",'
    if '"Belgium": "Europe/Brussels"' not in text:
        if old_tz not in text:
            raise SystemExit("Could not locate TZ table for Belgium patch")
        text = text.replace(old_tz, new_tz, 1)

    marker = '        elif country == "Czech Republic":'
    belgium = '''        elif country == "Belgium":
            # Belgium has no general nationwide Sunday/public-holiday or weekend
            # driving ban for standard HGV freight traffic. Keep the feed empty
            # rather than creating misleading calendar events.
            pass
'''
    if 'elif country == "Belgium":' not in text:
        if marker not in text:
            raise SystemExit("Could not locate country rules insertion point")
        text = text.replace(marker, belgium + marker, 1)

    old_lux = '''        elif country == "Luxembourg":
            if d.weekday() == 5:
                add(E,country,"HGV ban — Saturday towards France",d,"21:30","24:00",">7.5t; direction France.")
                add(E,country,"HGV ban — Saturday towards Germany",d,"23:30","24:00",">7.5t; direction Germany.")
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","21:45",">7.5t; direction-specific rules and exemptions apply.")
'''
    new_lux = '''        elif country == "Luxembourg":
            fr_holiday = d in holiday_dates("France", years)
            de_holiday = d in holiday_dates("Germany", years)
            next_day = d + timedelta(days=1)
            next_fr_holiday = next_day in holiday_dates("France", years)
            next_de_holiday = next_day in holiday_dates("Germany", years)
            if d.weekday() == 6:
                add(E,country,"HGV ban — Sunday transit towards France",d,"00:00","21:45",">7.5t; transit towards France. Domestic traffic and traffic with a Luxembourg destination are not covered.")
                add(E,country,"HGV ban — Sunday transit towards Germany",d,"00:00","21:45",">7.5t; transit towards Germany. Domestic traffic and traffic with a Luxembourg destination are not covered.")
            if d.weekday() == 5 or next_fr_holiday:
                add(E,country,"HGV ban — transit towards France",d,"21:30","24:00",">7.5t; transit towards France. Applies Saturday evenings and the eve of relevant French public holidays.")
            if d.weekday() == 5 or next_de_holiday:
                add(E,country,"HGV ban — transit towards Germany",d,"23:30","24:00",">7.5t; transit towards Germany. Applies Saturday evenings and the eve of relevant German public holidays.")
            if fr_holiday:
                add(E,country,"HGV ban — public holiday transit towards France",d,"00:00","21:45",">7.5t; transit towards France; French public holiday.")
            if de_holiday:
                add(E,country,"HGV ban — public holiday transit towards Germany",d,"00:00","21:45",">7.5t; transit towards Germany; German public holiday.")
'''
    if old_lux in text:
        text = text.replace(old_lux, new_lux, 1)
    elif 'HGV ban — public holiday transit towards France' not in text:
        raise SystemExit("Could not locate Luxembourg rules block")

    # Hungary: model cross-midnight weekend/public-holiday restrictions at source.
    # The existing add() helper cannot represent an end on the following day,
    # so add a small span helper and use it for Hungary's continuous periods.
    add_marker = '''    events.append((a, b, country, title, desc))\n\n\ndef add_holiday_rules'''
    add_replacement = '''    events.append((a, b, country, title, desc))\n\n\ndef add_span(events, country, title, start_day, start, end_day, end, desc):\n    tz = TZ[country]\n    def make(day, hm):\n        if hm == "24:00":\n            return datetime(day.year, day.month, day.day, 0, 0, tzinfo=ZoneInfo(tz)) + timedelta(days=1)\n        h, m = map(int, hm.split(":"))\n        return datetime(day.year, day.month, day.day, h, m, tzinfo=ZoneInfo(tz))\n    a, b = make(start_day, start), make(end_day, end)\n    if b <= a:\n        b += timedelta(days=1)\n    if b <= NOW:\n        return\n    events.append((a, b, country, title, desc))\n\n\ndef add_holiday_rules'''
    if 'def add_span(events, country, title' not in text:
        if add_marker not in text:
            raise SystemExit("Could not locate add() helper for Hungary span patch")
        text = text.replace(add_marker, add_replacement, 1)

    hungary_branch = '''        elif country == "Hungary":
            # Summer weekends run continuously from Saturday 15:00 to Sunday 22:00.
            # Public-holiday restrictions begin at 22:00 on the preceding day and
            # run to 22:00 on the holiday (unless the holiday is Sunday, which is
            # already covered by the Sunday rule).
            if d.weekday() == 5:
                end_day = d + timedelta(days=1)
                if date(d.year,7,1) <= d <= date(d.year,8,31):
                    add_span(E,country,"HGV ban — summer weekend",d,"15:00",end_day,"22:00",">7.5t; summer restriction runs from Saturday 15:00 to Sunday 22:00.")
                else:
                    add_span(E,country,"HGV ban — weekend",d,"22:00",end_day,"22:00",">7.5t; winter-period weekend restriction runs from Saturday 22:00 to Sunday 22:00. International Euro 3+ exemptions may apply in winter.")
            if h and d.weekday() != 6:
                prev = d - timedelta(days=1)
                add_span(E,country,"HGV ban — public holiday",prev,"22:00",d,"22:00",">7.5t; public-holiday and consecutive-holiday rules apply.")
'''
    pattern = r'        elif country == "Hungary":.*?(?=        elif country == "Luxembourg":)'
    text, n = re.subn(pattern, hungary_branch, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"Expected Hungary branch not found (matches={n})")

    # Put the manual temporary-exception warning directly on every Hungarian
    # appointment, including the combined feed. This is deliberately a reminder,
    # not an attempt to guess future government suspensions.
    make_ics_marker = '''              f"SUMMARY:{esc(c+' — '+t)}",f"DESCRIPTION:{esc(d)}","STATUS:CONFIRMED","END:VEVENT"]'''
    make_ics_replacement = '''              f"SUMMARY:{esc(c+' — '+t)}",\n              f"DESCRIPTION:{esc(d + (' IMPORTANT: Temporary Hungarian government suspensions or partial releases may change this specific restriction. Check the latest official Hungarian information before dispatch.' if c == 'Hungary' else ''))}",\n              "STATUS:CONFIRMED","END:VEVENT"]'''
    if 'Temporary Hungarian government suspensions or partial releases may change this specific restriction.' not in text:
        if make_ics_marker not in text:
            raise SystemExit("Could not locate ICS description line for Hungary alert patch")
        text = text.replace(make_ics_marker, make_ics_replacement, 1)

    # Keep the source timezone table patch idempotent and write the result.
    GEN.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    print("Applied verified Belgium, Luxembourg, Slovakia and Hungary country rules")
