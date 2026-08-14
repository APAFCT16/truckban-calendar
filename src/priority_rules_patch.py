from pathlib import Path
import re

p = Path("src/calendar_generator.py")
s = p.read_text(encoding="utf-8")

# Replace the entire France branch between country sections. This keeps the
# verified 2026 rules independent of the stale generic TruckBAN summer dates.
france_branch = '''        elif country == "France":
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
pattern = r'        elif country == "France":.*?(?=        elif country == "Czech Republic":)'
s2, n = re.subn(pattern, france_branch, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"Expected France branch not found (matches={n})")
p.write_text(s2, encoding="utf-8")
print("Applied verified France 2026 rules")
