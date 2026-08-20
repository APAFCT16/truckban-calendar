from pathlib import Path

P = Path("src/calendar_generator.py")
s = P.read_text(encoding="utf-8")

old = '''        elif country == "Slovenia":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"08:00","22:00",">7.5t on affected road sections.")
            summer_start = last_weekday(d.year,6,5); summer_end = date(d.year,9,7)
            if summer_start <= d <= summer_end and d.weekday() == 5: add(E,country,"HGV ban — summer Saturday",d,"08:00","13:00",">7.5t on affected road sections; some listed routes have 06:00–16:00 restrictions.")
'''

new = '''        elif country == "Slovenia":
            # General national restriction: Sundays, public holidays and other
            # non-working days, 08:00-22:00 local time. Good Friday is a
            # special case: 14:00-22:00.
            if d.weekday() == 6 or h:
                add(E,country,"HGV ban — Sunday/public holiday",d,"08:00","22:00",">7.5t on affected road sections; statutory exemptions apply.")

            # Good Friday is not consistently exposed as a public holiday by
            # the Python holidays package, so calculate Easter explicitly.
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

            # Tourist season runs from the last weekend of June through the
            # first weekend of September. In 2026 this is 27 June-6 September.
            # The ordinary Saturday restriction is 08:00-13:00. Five listed
            # coastal/priority routes have the stronger 06:00-16:00 Saturday
            # restriction. Sunday/holiday remains 08:00-22:00.
            summer_start = last_weekday(d.year,6,5) + timedelta(days=1)
            summer_end = last_weekday(d.year,9,6)
            if summer_start <= d <= summer_end and d.weekday() == 5:
                add(E,country,"HGV ban — summer Saturday",d,"08:00","13:00",">7.5t on affected road sections; tourist-season Saturday restriction.")
                add(E,country,"HGV ban — summer Saturday — listed routes",d,"06:00","16:00",">7.5t on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača/Fernetiči, H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane; tourist-season route-specific restriction.")
'''

if old not in s:
    raise SystemExit("Expected Slovenia generator block was not found; refusing to patch.")

P.write_text(s.replace(old, new, 1), encoding="utf-8")

# Update the country-feed description so the published feed documents the
# verified Slovenia framework rather than the old abbreviated wording.
F = Path("src/country_feeds.py")
f = F.read_text(encoding="utf-8")
old_desc = '    "Slovenia": "Slovenia: HGV restrictions apply Sundays/public holidays 08:00-22:00, plus tourist-season Saturday restrictions.",\n'
new_desc = '    "Slovenia": "Slovenia: HGVs over 7.5t are restricted Sundays, public holidays and non-working days 08:00-22:00, and on the Friday before Easter 14:00-22:00. During the tourist season (last weekend of June through first weekend of September; 27 June-6 September in 2026), Saturdays are restricted 08:00-13:00 generally, with 06:00-16:00 on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača-Fernetiči, H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane. Statutory exemptions and route-specific rules apply; this recurring feed represents the national framework only.",\n'
if old_desc in f:
    F.write_text(f.replace(old_desc, new_desc, 1), encoding="utf-8")
