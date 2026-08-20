from pathlib import Path

# This patch is intentionally idempotent: the workflow applies it after checkout
# on every run. Keep all edits line-safe so a country description can never
# corrupt country_feeds.py's CRLF join or Python syntax.

GENERATOR = Path("src/calendar_generator.py")
COUNTRY_FEEDS = Path("src/country_feeds.py")


def patch_generator():
    s = GENERATOR.read_text(encoding="utf-8")
    start = s.index('        elif country == "Slovenia":')
    end = s.index('        elif country == "Switzerland":', start)

    new = '''        elif country == "Slovenia":
            # Slovenia national HGV restriction: Sundays and public holidays
            # are 08:00-22:00 local. Good Friday is a separate 14:00-22:00
            # special restriction.
            holiday_names = {
                (1, 1): "New Year's Day",
                (1, 2): "New Year Holiday",
                (2, 8): "Prešeren Day",
                (4, 27): "Day of Uprising Against the Occupation",
                (5, 1): "Labour Day",
                (5, 2): "Labour Day",
                (6, 25): "Statehood Day",
                (8, 15): "Assumption Day",
                (10, 31): "Reformation Day",
                (11, 1): "Remembrance Day",
                (12, 25): "Christmas Day",
                (12, 26): "Independence and Unity Day",
            }
            holiday_label = holiday_names.get((d.month, d.day))

            # Calculate Easter explicitly so Easter Monday and Good Friday are
            # represented consistently even if the holidays package changes.
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
                add(E,country,"HGV ban — Good Friday",d,"14:00","22:00",">7.5t on affected road sections; Good Friday special restriction.")
            elif d == easter:
                add(E,country,"HGV ban — Easter Sunday",d,"08:00","22:00",">7.5t on affected road sections; Easter Sunday public-holiday restriction; statutory exemptions apply.")
            elif d == easter + timedelta(days=1):
                add(E,country,"HGV ban — Easter Monday",d,"08:00","22:00",">7.5t on affected road sections; Easter Monday public-holiday restriction; statutory exemptions apply.")
            elif holiday_label:
                add(E,country,f"HGV ban — {holiday_label}",d,"08:00","22:00",f">7.5t on affected road sections; {holiday_label} public-holiday restriction; statutory exemptions apply.")
            elif d.weekday() == 6:
                add(E,country,"HGV ban — Sunday",d,"08:00","22:00",">7.5t on affected road sections; Sunday restriction; statutory exemptions apply.")

            # Tourist season runs from the last weekend of June through the
            # first weekend of September. The first Saturday is therefore the
            # last Saturday in June (26 June 2027). Ordinary Saturday is
            # 08:00-13:00; listed routes are separately 06:00-16:00.
            summer_start = last_weekday(d.year,6,5)
            summer_end = last_weekday(d.year,9,6)
            if summer_start <= d <= summer_end and d.weekday() == 5:
                add(E,country,"HGV ban — summer Saturday",d,"08:00","13:00",">7.5t on affected road sections; tourist-season Saturday restriction.")
                add(E,country,"HGV ban — summer Saturday — listed routes",d,"06:00","16:00",">7.5t on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača/Fernetiči, H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane; tourist-season route-specific restriction.")
'''
    s = s[:start] + new + s[end:]

    # Romania: add the recurring summer Friday restrictions from Order
    # 1249/132/2018. These are route-specific and direction-specific on A2.
    start = s.index('        elif country == "Romania":')
    end = s.index('        d += timedelta(days=1)', start)
    new = '''        elif country == "Romania":
            # Romania is route-specific. The recurring national feed represents
            # only the four road sectors listed in Annex 1 to Order 1249/132/2018:
            # A2, DN7, DN39 and DN22C. Direction is material on A2 and DN22C.
            # Public-holiday restrictions apply on the eve and the holiday itself;
            # seasonal tourist restrictions add Friday-Sunday windows in July-August.
            apr_sep = date(d.year, 4, 1) <= d <= date(d.year, 9, 30)
            jul_aug = date(d.year, 7, 1) <= d <= date(d.year, 8, 31)

            if apr_sep:
                if h:
                    add(E,country,"HGV ban — A2 — public holiday — both directions",d,"06:00","22:00",">7.5t; A2 București (DNCB)–Fundulea–Lehliu–Fetești–Cernavodă–Constanța (A4), both directions; statutory exemptions apply.")
                    add(E,country,"HGV ban — DN39 — public holiday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea (DN39A)–Mangalia, both directions; statutory exemptions apply.")
                if d.weekday() == 6:
                    add(E,country,"HGV ban — DN7 — Sunday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; Sunday restriction.")
                    add(E,country,"HGV ban — DN39 — Sunday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; Sunday restriction.")
                    add(E,country,"HGV ban — A2 — Sunday — both directions",d,"06:00","22:00",">7.5t; A2 București–Constanța, both directions; Sunday restriction.")

                # Summer Friday restrictions, 1 July-31 August:
                # A2 București→Constanța: 12:00-22:00 local (09:00-19:00 UTC).
                # DN7 both directions: 18:00-22:00 local (15:00-19:00 UTC).
                # DN39 both directions: 06:00-22:00 local (03:00-19:00 UTC).
                if d.weekday() == 4 and jul_aug:
                    add(E,country,"HGV ban — A2 — summer Friday — București→Constanța",d,"12:00","22:00",">7.5t; A2 București→Constanța, summer Friday restriction 1 July–31 August under Order 1249/132/2018.")
                    add(E,country,"HGV ban — DN7 — summer Friday — both directions",d,"18:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer Friday restriction 1 July–31 August under Order 1249/132/2018.")
                    add(E,country,"HGV ban — DN39 — summer Friday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer Friday restriction 1 July–31 August under Order 1249/132/2018.")

                if d.weekday() == 5 and jul_aug:
                    add(E,country,"HGV ban — A2 — summer Saturday — București→Constanța",d,"06:00","22:00",">7.5t; A2 București→Constanța, summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN7 — summer Saturday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN39 — summer Saturday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer restriction 1 July–31 August.")
                if d.weekday() == 6 and jul_aug:
                    add(E,country,"HGV ban — A2 — summer Sunday — Constanța→București",d,"06:00","22:00",">7.5t; A2 Constanța→București, summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN7 — summer Sunday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN39 — summer Sunday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN22C — summer Sunday — Murfatlar→Cernavodă",d,"06:00","22:00",">7.5t; DN22C Murfatlar (DN3)→Cernavodă (A2), summer restriction 1 July–31 August; statutory exemptions apply.")
                elif d.weekday() == 0 and jul_aug:
                    add(E,country,"HGV ban — A2 — summer Monday — Constanța→București",d,"12:00","22:00",">7.5t; A2 Constanța→București, summer restriction 1 July–31 August; statutory exemptions apply.")
'''
    GENERATOR.write_text(s[:start] + new + s[end:], encoding="utf-8")


def patch_country_feed_description():
    description = (
        "Slovenia: HGVs over 7.5t are restricted Sundays and public holidays 08:00-22:00, "
        "with Good Friday 14:00-22:00. During the tourist season (last weekend of June through "
        "first weekend of September), Saturdays are restricted 08:00-13:00 generally, with "
        "06:00-16:00 on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača-Fernetiči, "
        "H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane. "
        "Statutory exemptions and route-specific rules apply; this feed represents the recurring "
        "national framework only."
    )
    f = COUNTRY_FEEDS.read_text(encoding="utf-8")
    lines = f.splitlines()
    replacement = f'    "Slovenia": "{description}",'

    for i, line in enumerate(lines):
        if line.lstrip().startswith('"Slovenia":'):
            lines[i] = replacement
            COUNTRY_FEEDS.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return

    for i, line in enumerate(lines):
        if line.lstrip().startswith('"Croatia":'):
            lines.insert(i, replacement)
            COUNTRY_FEEDS.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return

    raise RuntimeError("Could not find a safe insertion point for Slovenia country description")


def patch_romania_description():
    description = (
        "Romania: route-specific HGV restrictions apply to vehicles over 7.5t on four named road sectors under "
        "Order 1249/132/2018: A2 București–Constanța, DN7 Pitești–Râmnicu Vâlcea–Veștem, DN39 Agigea–Mangalia "
        "and DN22C Murfatlar–Cernavodă. A2 and DN39 have public-holiday restrictions from 1 April to 30 September; "
        "DN7 is restricted on public holidays and their eves year-round. From 1 July to 31 August, additional "
        "tourist-season restrictions apply by route and direction: A2 Friday/Saturday București→Constanța and "
        "Sunday/Monday Constanța→București, DN7 Friday-Sunday both directions, DN39 Friday-Sunday both directions, "
        "and DN22C Sunday Murfatlar→Cernavodă. Statutory exemptions and temporary road-specific measures apply; "
        "this feed represents the recurring national route-restriction calendar only."
    )
    f = COUNTRY_FEEDS.read_text(encoding="utf-8")
    lines = f.splitlines()
    replacement = f'    "Romania": "{description}",'
    for i, line in enumerate(lines):
        if line.lstrip().startswith('"Romania":'):
            lines[i] = replacement
            COUNTRY_FEEDS.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise RuntimeError("Could not find Romania country description")


patch_generator()
patch_country_feed_description()
patch_romania_description()
print("Applied verified Slovenia rules and Romanian summer Friday rules safely.")
