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
            # France: permanent national rule is Saturday/holiday eve 22:00
            # through Sunday/public holiday 22:00. The 2026 summer Saturday
            # additions are five specific Saturdays, not every Saturday in a
            # date range. Source: French 2026 ministerial decree.
            if d.weekday() == 5:
                add(E,country,"HGV ban — Saturday",d,"22:00","24:00",">7.5t goods vehicles; national weekend restriction."
                    " The following Sunday continues the ban to 22:00.")
            if h and d.weekday() != 6:
                add(E,country,"HGV ban — public holiday",d,"00:00","22:00",">7.5t goods vehicles; national public-holiday restriction.")
                prev = d - timedelta(days=1)
                add(E,country,"HGV ban — holiday eve",prev,"22:00","24:00",">7.5t goods vehicles; national holiday-eve restriction.")
            elif d.weekday() == 6:
                add(E,country,"HGV ban — Sunday",d,"00:00","22:00",">7.5t goods vehicles; national Sunday restriction.")
            summer_2026 = {date(2026,7,11), date(2026,7,18), date(2026,7,25), date(2026,8,1), date(2026,8,8)}
            if d in summer_2026 and d.weekday() == 5:
                add(E,country,"HGV ban — 2026 summer Saturday",d,"07:00","19:00",">7.5t goods vehicles; additional summer restriction across the metropolitan France road network.")
'''
if old not in s:
    raise SystemExit("Expected France rule block was not found; refusing to modify generator")
p.write_text(s.replace(old, new), encoding="utf-8")
print("Applied verified France 2026 rules")
