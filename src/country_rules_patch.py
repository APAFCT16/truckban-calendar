# Verified Belgium, Luxembourg and Slovakia country-specific rules.
from pathlib import Path

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

    marker_sk = '        elif country == "Slovenia":'
    old_sk = '''        elif country == "Slovakia":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t on motorways, trunk roads and Class 1 roads.")
            if d.weekday() == 5 and date(d.year,7,1) <= d <= date(d.year,8,31): add(E,country,"HGV ban — summer Saturday",d,"07:00","19:00",">7.5t on motorways, trunk roads and Class 1 roads.")
'''
    new_sk = '''        elif country == "Slovakia":
            # 2026 transition: until 31 Aug the ban is 00:00-22:00 on Sundays/public
            # holidays and 07:00-19:00 on summer Saturdays. From 1 Sep 2026 the
            # Sunday/public-holiday start moves to 06:00 and the summer Saturday
            # start moves to 09:00 (summer Saturday end remains 19:00).
            if d >= date(2026,9,1):
                if d.weekday() == 6 or h:
                    add(E,country,"HGV ban — Sunday/public holiday",d,"06:00","22:00",">7.5t and >3.5t truck combinations on motorways, trunk roads and Class 1 roads; 2026 rules from 1 September.")
                if d.weekday() == 5 and date(d.year,7,1) <= d <= date(d.year,8,31):
                    add(E,country,"HGV ban — summer Saturday",d,"09:00","19:00",">7.5t and >3.5t truck combinations on motorways, trunk roads and Class 1 roads; 2026 rules from 1 September.")
            else:
                if d.weekday() == 6 or h:
                    add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t and >3.5t truck combinations on motorways, trunk roads and Class 1 roads; rules in force before 1 September 2026.")
                if d.weekday() == 5 and date(d.year,7,1) <= d <= date(d.year,8,31):
                    add(E,country,"HGV ban — summer Saturday",d,"07:00","19:00",">7.5t and >3.5t truck combinations on motorways, trunk roads and Class 1 roads; rules in force before 1 September 2026.")
'''
    if old_sk in text:
        text = text.replace(old_sk, new_sk, 1)
    elif '2026 transition: until 31 Aug' not in text:
        if marker_sk not in text:
            raise SystemExit("Could not locate Slovakia rules block")
        text = text.replace(marker_sk, new_sk + marker_sk, 1)

    GEN.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    print("Applied verified Belgium, Luxembourg and Slovakia country rules")
