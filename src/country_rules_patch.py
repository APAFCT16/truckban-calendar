from pathlib import Path
import re

GEN = Path("src/calendar_generator.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

    # Belgium timezone + explicit no-event branch.
    text = text.replace(
        '"Austria": "Europe/Vienna", "Croatia": "Europe/Zagreb", "Czech Republic": "Europe/Prague",',
        '"Austria": "Europe/Vienna", "Belgium": "Europe/Brussels", "Croatia": "Europe/Zagreb", "Czech Republic": "Europe/Prague",',
        1,
    )
    if 'elif country == "Belgium":' not in text:
        marker = '        elif country == "Czech Republic":'
        if marker not in text:
            raise SystemExit("Could not locate Czech Republic branch for Belgium patch")
        belgium = '''        elif country == "Belgium":
            # No general nationwide Sunday/public-holiday HGV ban for standard
            # freight traffic; keep this feed empty rather than inventing events.
            pass
'''
        text = text.replace(marker, belgium + marker, 1)

    # Luxembourg: direction-specific transit rules.
    lux_branch = '''        elif country == "Luxembourg":
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
    text, n = re.subn(r'        elif country == "Luxembourg":.*?(?=        elif country == "Poland":)', lux_branch, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"Expected Luxembourg branch not found (matches={n})")

    # Add a helper capable of representing a restriction that crosses midnight.
    # Do not depend on the workflow's runtime-clock sed step here: this helper
    # is inserted after that step has already run.
    if 'def add_span(events, country, title, start_day' not in text:
        marker = '''    events.append((a, b, country, title, desc))\n\n\ndef add_holiday_rules'''
        replacement = '''    events.append((a, b, country, title, desc))\n\n\ndef add_span(events, country, title, start_day, start, end_day, end, desc):\n    tz = TZ[country]\n    def make(day, hm):\n        if hm == "24:00":\n            return datetime(day.year, day.month, day.day, 0, 0, tzinfo=ZoneInfo(tz)) + timedelta(days=1)\n        h, m = map(int, hm.split(":"))\n        return datetime(day.year, day.month, day.day, h, m, tzinfo=ZoneInfo(tz))\n    a, b = make(start_day, start), make(end_day, end)\n    if b <= a:\n        b += timedelta(days=1)\n    if b <= datetime.now(timezone.utc):\n        return\n    events.append((a, b, country, title, desc))\n\n\ndef add_holiday_rules'''
        if marker not in text:
            raise SystemExit("Could not locate add() helper")
        text = text.replace(marker, replacement, 1)

    # Hungary: continuous Saturday-to-Sunday periods and holiday-eve-to-holiday
    # periods. Temporary government suspensions are handled as a manual-check
    # warning rather than guessed automatically.
    hungary_branch = '''        elif country == "Hungary":
            warning = " IMPORTANT: Temporary Hungarian government suspensions or partial releases may change this specific restriction. Check the latest official Hungarian information before dispatch."
            if d.weekday() == 5:
                end_day = d + timedelta(days=1)
                if date(d.year,7,1) <= d <= date(d.year,8,31):
                    add_span(E,country,"HGV ban — summer weekend",d,"15:00",end_day,"22:00",">7.5t; summer restriction runs from Saturday 15:00 to Sunday 22:00." + warning)
                else:
                    add_span(E,country,"HGV ban — weekend",d,"22:00",end_day,"22:00",">7.5t; winter-period weekend restriction runs from Saturday 22:00 to Sunday 22:00. International Euro 3+ exemptions may apply in winter." + warning)
            if h and d.weekday() != 6:
                prev = d - timedelta(days=1)
                add_span(E,country,"HGV ban — public holiday",prev,"22:00",d,"22:00",">7.5t; public-holiday and consecutive-holiday rules apply." + warning)
'''
    text, n = re.subn(r'        elif country == "Hungary":.*?(?=        elif country == "Luxembourg":)', hungary_branch, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"Expected Hungary branch not found (matches={n})")

    # Czechia: use the statutory road scope and include the 3.5t-with-trailer
    # vehicle class in every event description.
    old_czech = '''        elif country == "Czech Republic":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"13:00","22:00",">7.5t on motorways, expressways and 1st-class roads.")
            if date(d.year,7,1) <= d <= date(d.year,8,31):
                if d.weekday() == 4: add(E,country,"HGV ban — summer Friday",d,"17:00","21:00",">7.5t on affected roads.")
                if d.weekday() == 5: add(E,country,"HGV ban — summer Saturday",d,"07:00","13:00",">7.5t on affected roads.")
'''
    new_czech = '''        elif country == "Czech Republic":
            scope = ">7.5t, plus vehicles over 3.5t with a trailer/semi-trailer, on motorways and Class I roads; statutory exemptions apply."
            if d.weekday() == 6 or h:
                add(E,country,"HGV ban — Sunday/public holiday",d,"13:00","22:00",scope)
            if date(d.year,7,1) <= d <= date(d.year,8,31):
                if d.weekday() == 4:
                    add(E,country,"HGV ban — summer Friday",d,"17:00","21:00",scope)
                if d.weekday() == 5:
                    add(E,country,"HGV ban — summer Saturday",d,"07:00","13:00",scope)
'''
    if old_czech not in text:
        raise SystemExit("Expected Czech Republic branch not found")
    text = text.replace(old_czech, new_czech, 1)

    GEN.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    print("Applied verified Belgium, Luxembourg, Hungary and Czechia country rules")
