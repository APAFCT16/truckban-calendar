from pathlib import Path

GEN = Path("src/calendar_generator.py")

text = GEN.read_text(encoding="utf-8")
old = '''        elif country == "Switzerland":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","24:00",">3.5t HGVs and specified combinations; cantonal holiday rules and exemptions apply.")
'''
new = '''        elif country == "Switzerland":
            scope = ">3.5t permissible total weight; articulated motor vehicles over 5t permissible total towing weight; or vehicles towing a trailer over 3.5t permissible total weight. Statutory exemptions apply."
            if d.weekday() == 6 or h:
                add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",scope)
'''
if old not in text:
    raise SystemExit("Expected Switzerland branch not found exactly")
GEN.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Corrected Switzerland Sunday/public-holiday event window to 00:00-22:00")
