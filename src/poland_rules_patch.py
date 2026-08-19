from pathlib import Path
import re

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")
    start = text.find('        elif country == "Poland":')
    end = text.find('        elif country == "Slovakia":', start)
    if start < 0 or end < 0:
        raise SystemExit("Could not locate Poland branch")

    replacement = '''        elif country == "Poland":
            # Poland's national periodic restriction applies to vehicles and
            # combinations with permissible maximum mass over 12t, excluding
            # buses. The statutory holiday list in the traffic-ban regulation
            # is narrower than the general Polish public-holiday calendar: it
            # does NOT include 6 January (Epiphany).
            restricted_holidays = {
                x for x in hol
                if (x.month == 1 and x.day == 1)
                or (x.month == 5 and x.day in (1, 3))
                or (x.month == 8 and x.day == 15)
                or (x.month == 11 and x.day in (1, 11))
                or (x.month == 12 and x.day in (25, 26))
            }

            # The two Easter days and Pentecost/Corpus Christi are movable;
            # derive them from the Polish holiday package rather than relying
            # on month numbers. The package contains the exact Polish dates.
            easter_days = {x for x in hol if x.weekday() == 6 and x.month in (3, 4)}
            for easter_sunday in easter_days:
                if easter_sunday in hol and easter_sunday + timedelta(days=1) in hol:
                    restricted_holidays.add(easter_sunday)
                    restricted_holidays.add(easter_sunday + timedelta(days=1))
                    restricted_holidays.add(easter_sunday + timedelta(days=49))
                    restricted_holidays.add(easter_sunday + timedelta(days=60))

            # §2(2): 18:00-22:00 on the day before the listed holidays b-j.
            # This intentionally excludes New Year's Day and Christmas Day/
            # Boxing Day, which are listed in §2(1) but not in §2(2).
            eve_targets = {
                x for x in restricted_holidays
                if not (x.month == 1 and x.day == 1)
                and not (x.month == 12 and x.day in (25, 26))
            }
            if d in restricted_holidays:
                add(E,country,"HGV ban — public holiday",d,"08:00","22:00",">12t permissible maximum mass; nationwide, subject to statutory exemptions. Poland national restriction under the 31 July 2007 regulation.")
            if d + timedelta(days=1) in eve_targets:
                add(E,country,"HGV ban — public holiday eve",d,"18:00","22:00",">12t permissible maximum mass; nationwide, subject to statutory exemptions. Restriction applies on the day preceding the listed holiday under §2(2).")

            # §2(3): summer restriction runs from the Friday on which school
            # classes end (or the following Friday) through the last Sunday
            # before classes resume. The current Polish school calendars place
            # this at the final Friday of June through the final Sunday of
            # August; using the final Sunday is important because the prior
            # implementation stopped one day early.
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
    text = text[:start] + replacement + text[end:]
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
    print("Applied verified Poland HGV restriction rules")
