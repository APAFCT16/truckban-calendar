from pathlib import Path

GEN = Path("src/calendar_generator.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

    old = '''        elif country == "Croatia":
            if date(d.year,6,15) <= d <= date(d.year,9,15):
                if d.weekday() == 5: add(E,country,"HGV ban — summer Saturday",d,"04:00","14:00",">7.5t or >14m on specified main roads.")
                if d.weekday() == 6: add(E,country,"HGV ban — summer Sunday",d,"12:00","23:00",">7.5t or >14m on specified main roads.")
            if h and d.weekday() != 6: add(E,country,"HGV ban — public holiday",d,"14:00","23:00",">7.5t or >14m on specified main roads.")
'''

    new = '''        elif country == "Croatia":
            scope = ">7.5t or >14m on specified main roads and the Split/Zadar ferry-port approaches; statutory exemptions apply."

            # Standing summer restrictions: 15 June–15 September.
            if date(d.year,6,15) <= d <= date(d.year,9,15):
                if d.weekday() == 5:
                    add(E,country,"HGV ban — summer Saturday",d,"04:00","14:00",scope)
                if d.weekday() == 6:
                    add(E,country,"HGV ban — summer Sunday",d,"12:00","23:00",scope)

            # Croatian holiday rules are calendar-dependent and are not simply
            # "holiday = 14:00-23:00". The Order also covers Good Friday,
            # holiday eves, and Sunday/Friday compensating restrictions.
            # Calculate Easter Sunday deterministically so Good Friday and the
            # Easter sequence are represented even when Good Friday is not
            # exposed as a public holiday by the holidays library.
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
            good_friday = easter - timedelta(days=2)

            if d == good_friday:
                add(E,country,"HGV ban — Good Friday",d,"15:00","23:00",scope)

            # Eve of every public/religious holiday: 15:00-23:00. This includes
            # Holy Saturday as the eve of Easter Sunday.
            next_day = d + timedelta(days=1)
            if next_day in hol or next_day == easter:
                add(E,country,"HGV ban — holiday eve",d,"15:00","23:00",scope)

            # Public holiday itself: 14:00-23:00, including Sundays/Mondays.
            if h:
                add(E,country,"HGV ban — public holiday",d,"14:00","23:00",scope)

            # If the holiday or the last day of a consecutive holiday series is
            # Friday/Saturday, the following Sunday is restricted 12:00-23:00.
            if h and d.weekday() in (4, 5) and next_day not in hol:
                following_sunday = d + timedelta(days=6 - d.weekday())
                add(E,country,"HGV ban — holiday Sunday",following_sunday,"12:00","23:00",scope)

            # If a public holiday falls on Sunday or Monday, the preceding Friday
            # is restricted 15:00-23:00.
            if h and d.weekday() in (6, 0):
                preceding_friday = d - timedelta(days=(d.weekday() + 3) % 7)
                add(E,country,"HGV ban — pre-holiday Friday",preceding_friday,"15:00","23:00",scope)
'''

    if old not in text:
        raise SystemExit("Expected Croatia branch not found; refusing to patch")
    text = text.replace(old, new, 1)
    GEN.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    print("Applied Croatian Good Friday, holiday-eve and calendar-dependent holiday rules")
