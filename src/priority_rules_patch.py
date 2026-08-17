from pathlib import Path
import re

p = Path("src/calendar_generator.py")
s = p.read_text(encoding="utf-8")

# Replace the entire France branch with verified 2026 national rules.
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
s, n = re.subn(pattern, france_branch, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"Expected France branch not found (matches={n})")

# Replace Germany with the 2026 BMV rule and the current affected route list.
germany_branch = '''        elif country == "Germany":
            if d.weekday() == 6 or h:
                add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t and trucks with trailers; nationwide, subject to statutory exemptions. The Sunday/public-holiday ban applies to the entire road network.")
            if d.weekday() == 5 and date(d.year,7,1) <= d <= date(d.year,8,31):
                routes = ("A1 Erfttal–Leverkusen-West–Wuppertal–Kamener Kreuz–Münster–Lotte/Osnabrück and Bremen-Brinkum–Bremer Kreuz; A2 Oberhausen–Bad Oeynhausen; A3 Oberhausen–Köln-Ost and Mönchhof Dreieck–Frankfurter Kreuz–Nürnberg; A4 Kirchheimer Dreieck–Thüringen border at Herleshausen; A45 Dortmund-Süd–Westhofener Kreuz–Gambacher Kreuz–Seligenstädter Dreieck; A61 Meckenheim–Koblenz–Hockenheim; A67 Darmstädter Kreuz–Viernheimer Dreieck; A81 Stuttgart-Zuffenhausen–Gärtringen; A92 München-Feldmoching–Oberschleißheim and Neufahrn–Erding; A93 Inntal–Reischenhart; A99 Munich ring sections; A113 Schönefeld–Neukölln (towards Hamburg); A115 Zehlendorf–Funkturm; A831 Stuttgart-Vaihingen–Stuttgart; A980 Allgäu–Waltenhofen; A995 Sauerlach–München-Süd; B31 Stockach-Ost/A98–Sigmarszell/A96; B96/E251 Berlin border–B104 Neubrandenburg.")
                add(E,country,"HGV ban — summer Saturday",d,"07:00","20:00",">7.5t and trucks with trailers carrying goods commercially; ONLY on the specified motorway and federal-road sections, both directions. Affected routes: " + routes + " Exemptions apply.")
'''
pattern = r'        elif country == "Germany":.*?(?=        elif country == "France":)'
s, n = re.subn(pattern, germany_branch, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f"Expected Germany branch not found (matches={n})")

p.write_text(s, encoding="utf-8")
print("Applied verified France 2026 and Germany 2026 priority rules")
