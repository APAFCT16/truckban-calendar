from pathlib import Path

P = Path("src/calendar_generator.py")
s = P.read_text(encoding="utf-8")

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
            # represented consistently even if the holidays package changes
            # which religious dates it exposes.
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
            # first weekend of September. Therefore the first Saturday is the
            # last Saturday in June (26 June 2027), not the first Saturday in
            # July. The ordinary Saturday restriction is 08:00-13:00.
            summer_start = last_weekday(d.year,6,5)
            summer_end = last_weekday(d.year,9,6)
            if summer_start <= d <= summer_end and d.weekday() == 5:
                add(E,country,"HGV ban — summer Saturday",d,"08:00","13:00",">7.5t on affected road sections; tourist-season Saturday restriction.")
                add(E,country,"HGV ban — summer Saturday — listed routes",d,"06:00","16:00",">7.5t on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača/Fernetiči, H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane; tourist-season route-specific restriction.")
'''

s = s[:start] + new + s[end:]
P.write_text(s, encoding="utf-8")

# Keep the published Slovenia country-feed description aligned with the
# generator, including the holiday-specific and tourist-season framework.
F = Path("src/country_feeds.py")
f = F.read_text(encoding="utf-8")
slovenia_desc = '    "Slovenia": "Slovenia: HGVs over 7.5t are restricted Sundays and public holidays 08:00-22:00, with Good Friday 14:00-22:00. During the tourist season (last weekend of June through first weekend of September), Saturdays are restricted 08:00-13:00 generally, with 06:00-16:00 on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača-Fernetiči, H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane. Statutory exemptions and route-specific rules apply; this feed represents the recurring national framework only.",\n'
if '    "Slovenia":' in f:
    lines = f.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('"Slovenia":'):
            lines[i] = slovenia_desc.rstrip("\\n")
            break
    f = "\\n".join(lines) + "\\n"
else:
    marker = '    "Croatia":'
    idx = f.index(marker)
    line_end = f.index("\\n", idx)
    f = f[:line_end + 1] + slovenia_desc + f[line_end + 1:]
F.write_text(f, encoding="utf-8")
