from pathlib import Path
import re

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")


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
    if 'def add_span(events, country, title, start_day' not in text:
        marker = '''    events.append((a, b, country, title, desc))\n\n\ndef add_holiday_rules'''
        replacement = '''    events.append((a, b, country, title, desc))\n\n\ndef add_span(events, country, title, start_day, start, end_day, end, desc):\n    tz = TZ[country]\n    def make(day, hm):\n        if hm == "24:00":\n            return datetime(day.year, day.month, day.day, 0, 0, tzinfo=ZoneInfo(tz)) + timedelta(days=1)\n        h, m = map(int, hm.split(":"))\n        return datetime(day.year, day.month, day.day, h, m, tzinfo=ZoneInfo(tz))\n    a, b = make(start_day, start), make(end_day, end)\n    if b <= a:\n        b += timedelta(days=1)\n    if b <= datetime.now(timezone.utc):\n        return\n    events.append((a, b, country, title, desc))\n\n\ndef add_holiday_rules'''
        if marker not in text:
            raise SystemExit("Could not locate add() helper")
        text = text.replace(marker, replacement, 1)

    # Hungary: continuous Saturday-to-Sunday periods and holiday-eve-to-holiday periods.
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

    # Czechia: use the statutory road scope and include the 3.5t-with-trailer vehicle class.
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

    # Poland: statutory holiday list, including Easter Sunday/Monday, Pentecost
    # and Corpus Christi; explicit holiday eves; and the final summer Sunday.
    # 6 January is a public holiday but is deliberately NOT a traffic-ban holiday.
    poland_branch = '''        elif country == "Poland":
            restricted_holidays = {
                x for x in hol
                if (x.month == 1 and x.day == 1)
                or (x.month == 5 and x.day in (1, 3))
                or (x.month == 8 and x.day == 15)
                or (x.month == 11 and x.day in (1, 11))
                or (x.month == 12 and x.day in (25, 26))
            }

            # Add the movable statutory traffic-ban holidays directly from the
            # Gregorian Easter calculation instead of relying on holiday-library
            # labels. This makes the recurring feed deterministic for future years.
            a = d.year
            aa = a % 19
            bb = a // 100
            cc = a % 100
            dd = bb // 4
            ee = bb % 4
            ff = (bb + 8) // 25
            gg = (bb - ff + 1) // 3
            hh = (19 * aa + bb - dd - gg + 15) % 30
            ii = cc // 4
            kk = cc % 4
            ll = (32 + 2 * ee + 2 * ii - hh - kk) % 7
            mm = (aa + 11 * hh + 22 * ll) // 451
            easter_month = (hh + ll - 7 * mm + 114) // 31
            easter_day = ((hh + ll - 7 * mm + 114) % 31) + 1
            easter = date(a, easter_month, easter_day)
            restricted_holidays.update({easter, easter + timedelta(days=1), easter + timedelta(days=49), easter + timedelta(days=60)})

            eve_targets = {
                x for x in restricted_holidays
                if not (x.month == 1 and x.day == 1)
                and not (x.month == 12 and x.day in (25, 26))
            }
            if d in restricted_holidays:
                add(E,country,"HGV ban — public holiday",d,"08:00","22:00",">12t permissible maximum mass; nationwide, subject to statutory exemptions. Poland national restriction under the 31 July 2007 regulation.")
            if d + timedelta(days=1) in eve_targets:
                add(E,country,"HGV ban — public holiday eve",d,"18:00","22:00",">12t permissible maximum mass; nationwide, subject to statutory exemptions. Restriction applies on the day preceding the listed holiday under §2(2).")

            summer_start = last_weekday(d.year,6,4)
            summer_end = last_weekday(d.year,8,6)
            if summer_start <= d <= summer_end:
                if d.weekday() == 4:
                    add(E,country,"HGV ban — summer Friday",d,"18:00","22:00",">12t permissible maximum mass; nationwide summer restriction. Statutory exemptions apply.")
                if d.weekday() == 5:
                    add(E,country,"HGV ban — summer Saturday",d,"08:00","14:00",">12t permissible maximum mass; nationwide summer restriction. Statutory exemptions apply.")
                if d.weekday() == 6:
                    add(E,country,"HGV ban — summer Sunday",d,"08:00","22:00",">12t permissible maximum mass; nationwide summer restriction. Statutory exemptions apply.")
'''
    text, n = re.subn(r'        elif country == "Poland":.*?(?=        elif country == "Slovakia":)', poland_branch, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"Expected Poland branch not found (matches={n})")

    GEN.write_text(text, encoding="utf-8")


def patch_feed_description():
    text = FEEDS.read_text(encoding="utf-8")
    if '"Poland":' in text:
        text = re.sub(r'    "Poland": ".*?",\n', '', text, count=1)
    marker = '    "Portugal": '
    pos = text.find(marker)
    if pos < 0:
        raise SystemExit("Could not locate Portugal description")
    desc = '    "Poland": "Poland: nationwide periodic HGV restrictions apply to vehicles and combinations over 12t permissible maximum mass, excluding buses. The national restriction is 08:00-22:00 on the specified public holidays; 18:00-22:00 on the eve of the specified holidays (excluding New Year and Christmas Day/Boxing Day); and during the summer period from the final Friday of June through the last Sunday of August, 18:00-22:00 Fridays, 08:00-14:00 Saturdays and 08:00-22:00 Sundays. 6 January (Epiphany) is a Polish public holiday but is not included in the HGV traffic-ban holiday list. Statutory exemptions include certain emergency, essential, perishable, dangerous-goods and other specified transport; this feed represents the recurring national restriction calendar only.",\n'
    text = text[:pos] + desc + text[pos:]
    FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_feed_description()
    print("Applied verified Belgium, Luxembourg, Hungary, Czechia and Poland country rules")
