from pathlib import Path

p = Path("src/calendar_generator.py")
s = p.read_text(encoding="utf-8")
old = '''        elif country == "France":
            if d.weekday() == 5: add(E,country,"HGV ban — Saturday",d,"22:00","24:00",">7.5t goods vehicles; general national weekend restriction.")
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t goods vehicles; general national restriction; route exemptions may apply.")
            if last_weekday(d.year,7,5) <= d <= last_weekday(d.year,8,5) and d.weekday() == 5:
                add(E,country,"HGV ban — summer Saturday",d,"07:00","19:00",">7.5t goods vehicles; additional summer restriction on the national network.")
'''
new = '''        elif country == "France":
            # Verified 2026 national rules. The five additional summer Saturdays
            # are specific dates; do not extrapolate them to every Saturday.
            if d.weekday() == 5:
                add(E,country,"HGV ban — Saturday",d,"22:00","24:00",">7.5t goods vehicles; national weekend restriction. The following Sunday continues the ban to 22:00. Île-de-France has additional route/direction restrictions not represented by this national event.")
            if h and d.weekday() != 6:
                add(E,country,"HGV ban — public holiday",d,"00:00","22:00",">7.5t goods vehicles; national public-holiday restriction. Île-de-France has additional route/direction restrictions.")
                prev = d - timedelta(days=1)
                add(E,country,"HGV ban — holiday eve",prev,"22:00","24:00",">7.5t goods vehicles; national holiday-eve restriction. Île-de-France has additional route/direction restrictions.")
            elif d.weekday() == 6:
                add(E,country,"HGV ban — Sunday",d,"00:00","22:00",">7.5t goods vehicles; national Sunday restriction. Île-de-France has additional route/direction restrictions.")
            summer_2026 = {date(2026,7,11), date(2026,7,18), date(2026,7,25), date(2026,8,1), date(2026,8,8)}
            if d in summer_2026 and d.weekday() == 5:
                add(E,country,"HGV ban — 2026 summer Saturday",d,"07:00","19:00",">7.5t goods vehicles; additional summer restriction across metropolitan France. Île-de-France and Auvergne-Rhône-Alpes route-specific rules also exist.")
'''
if old not in s:
    raise SystemExit("Expected France rule block was not found; refusing to modify generator")
s = s.replace(old, new)
old_de = '            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t and trucks with trailers; nationwide subject to exemptions.")'
new_de = '            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t and trucks with trailers; nationwide subject to exemptions. Germany summer Saturday restrictions apply only on specified routes: A1, A2, A3, A4, A5, A6, A7, A8, A9/E51, A10, A45, A61, A67, A81, A92, A93, A99, A113, A115, A831, A980, A995, B31 and B96/E251.")'
if old_de not in s:
    raise SystemExit("Expected Germany Sunday rule was not found; refusing to modify generator")
s = s.replace(old_de, new_de)
p.write_text(s, encoding="utf-8")
print("Applied verified France 2026 and Germany route-scope priority rules")
