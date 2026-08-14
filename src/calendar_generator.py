from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import calendar
import json
from zoneinfo import ZoneInfo

COUNTRIES_FILE = Path("countries.json")
DEBUG_DIR = Path("debug/truckban")
PUBLIC_DIR = Path("public")
BASE_URL = "https://truckban.eu/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139.0 Safari/537.36"

TZ = {
    "Austria": "Europe/Vienna", "Croatia": "Europe/Zagreb", "Czech Republic": "Europe/Prague",
    "France": "Europe/Paris", "Germany": "Europe/Berlin", "Hungary": "Europe/Budapest",
    "Italy": "Europe/Rome", "Liechtenstein": "Europe/Vaduz", "Luxembourg": "Europe/Luxembourg",
    "Poland": "Europe/Warsaw", "Romania": "Europe/Bucharest", "Slovakia": "Europe/Bratislava",
    "Slovenia": "Europe/Ljubljana", "Switzerland": "Europe/Zurich",
}

# The production calendar intentionally contains DISCRETE dated restrictions.
# Standing daily/night restrictions are documented in X-WR-CALDESC instead of
# creating hundreds of repetitive events that swamp Outlook.
SUPPORTED = set(TZ)
STANDING_RULES = (
    "Standing restrictions not repeated as individual events: Austria night ban 22:00-05:00 for HGVs >7.5t; "
    "Switzerland night ban 22:00-05:00 for HGVs >3.5t; local/route-specific night and environmental restrictions "
    "may also apply."
)

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        text = " ".join(data.split())
        if text: self.parts.append(text)
    def get_text(self): return "\n".join(self.parts)


def load_countries():
    return json.loads(COUNTRIES_FILE.read_text(encoding="utf-8"))["countries"]


def download_page(url):
    with urlopen(Request(url, headers={"User-Agent": UA}), timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def html_to_text(html):
    p = TextExtractor(); p.feed(html); return p.get_text()


def holiday_dates(country, years):
    try:
        import holidays
        codes = {"Austria":"AT","Croatia":"HR","Czech Republic":"CZ","France":"FR","Germany":"DE",
                 "Hungary":"HU","Italy":"IT","Liechtenstein":"LI","Luxembourg":"LU","Poland":"PL",
                 "Romania":"RO","Slovakia":"SK","Slovenia":"SI","Switzerland":"CH"}
        code = codes.get(country)
        if not code: return set()
        return {d for y in years for d in holidays.country_holidays(code, years=y).keys()}
    except Exception:
        return set()


def last_weekday(year, month, weekday):
    d = date(year, month, calendar.monthrange(year, month)[1])
    while d.weekday() != weekday: d -= timedelta(days=1)
    return d


def add(events, country, title, day, start, end, desc):
    tz = TZ[country]
    def make(hm):
        if hm == "24:00": return datetime(day.year, day.month, day.day, 0, 0, tzinfo=ZoneInfo(tz)) + timedelta(days=1)
        h, m = map(int, hm.split(":")); return datetime(day.year, day.month, day.day, h, m, tzinfo=ZoneInfo(tz))
    a, b = make(start), make(end)
    if b <= a: b += timedelta(days=1)
    if b <= NOW: return
    events.append((a, b, country, title, desc))


def add_holiday_rules(events, country, day, holidays_set, start, end, label, threshold):
    if day in holidays_set and day.weekday() != 6:
        add(events, country, label, day, start, end, threshold)


def country_events(country, today, stop):
    if country not in SUPPORTED: return []
    E = []; years = range(today.year, stop.year + 1); hol = holiday_dates(country, years)
    d = today
    while d <= stop:
        h = d in hol
        if country == "Austria":
            if d.weekday() == 5: add(E,country,"HGV ban — Saturday",d,"15:00","24:00",">7.5t / truck combinations; nationwide, subject to exemptions.")
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t / truck combinations; nationwide, subject to exemptions.")
        elif country == "Germany":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t and trucks with trailers; nationwide, subject to exemptions.")
            if d.weekday() == 5 and date(d.year,7,1) <= d <= date(d.year,8,31): add(E,country,"HGV ban — summer Saturday",d,"07:00","20:00",">7.5t / truck combinations on specified motorways and federal roads.")
        elif country == "France":
            if d.weekday() == 5: add(E,country,"HGV ban — Saturday",d,"22:00","24:00",">7.5t goods vehicles; general national weekend restriction.")
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t goods vehicles; general national restriction; route exemptions may apply.")
            if last_weekday(d.year,7,5) <= d <= last_weekday(d.year,8,5) and d.weekday() == 5:
                add(E,country,"HGV ban — summer Saturday",d,"07:00","19:00",">7.5t goods vehicles; additional summer restriction on the national network.")
        elif country == "Czech Republic":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"13:00","22:00",">7.5t on motorways, expressways and 1st-class roads.")
            if date(d.year,7,1) <= d <= date(d.year,8,31):
                if d.weekday() == 4: add(E,country,"HGV ban — summer Friday",d,"17:00","21:00",">7.5t on affected roads.")
                if d.weekday() == 5: add(E,country,"HGV ban — summer Saturday",d,"07:00","13:00",">7.5t on affected roads.")
        elif country == "Croatia":
            if date(d.year,6,15) <= d <= date(d.year,9,15):
                if d.weekday() == 5: add(E,country,"HGV ban — summer Saturday",d,"04:00","14:00",">7.5t or >14m on specified main roads.")
                if d.weekday() == 6: add(E,country,"HGV ban — summer Sunday",d,"12:00","23:00",">7.5t or >14m on specified main roads.")
            if h and d.weekday() != 6: add(E,country,"HGV ban — public holiday",d,"14:00","23:00",">7.5t or >14m on specified main roads.")
        elif country == "Hungary":
            # Use one continuous weekend event rather than separate Saturday/Sunday blocks.
            if d.weekday() == 5:
                end_day = d + timedelta(days=1)
                if date(d.year,7,1) <= d <= date(d.year,8,31):
                    add(E,country,"HGV ban — summer weekend",d,"15:00","22:00",">7.5t; summer restriction runs from Saturday 15:00 to Sunday 22:00.")
                else:
                    add(E,country,"HGV ban — weekend",d,"22:00","22:00",">7.5t; winter-period weekend restriction runs from Saturday 22:00 to Sunday 22:00. International Euro 3+ exemptions may apply in winter.")
            if h and d.weekday() != 6:
                add(E,country,"HGV ban — public holiday",d,"00:00","22:00",">7.5t; public-holiday and consecutive-holiday rules apply.")
        elif country == "Luxembourg":
            if d.weekday() == 5:
                add(E,country,"HGV ban — Saturday towards France",d,"21:30","24:00",">7.5t; direction France.")
                add(E,country,"HGV ban — Saturday towards Germany",d,"23:30","24:00",">7.5t; direction Germany.")
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","21:45",">7.5t; direction-specific rules and exemptions apply.")
        elif country == "Poland":
            summer = last_weekday(d.year,6,4) <= d <= last_weekday(d.year,8,6)
            if h and d.weekday() != 6: add(E,country,"HGV ban — public holiday",d,"08:00","22:00",">12t nationwide.")
            if summer:
                if d.weekday() == 4: add(E,country,"HGV ban — summer Friday",d,"18:00","22:00",">12t nationwide.")
                if d.weekday() == 5: add(E,country,"HGV ban — summer Saturday",d,"08:00","14:00",">12t nationwide.")
                if d.weekday() == 6: add(E,country,"HGV ban — summer Sunday",d,"08:00","22:00",">12t nationwide.")
        elif country == "Slovakia":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t on motorways, trunk roads and Class 1 roads.")
            if d.weekday() == 5 and date(d.year,7,1) <= d <= date(d.year,8,31): add(E,country,"HGV ban — summer Saturday",d,"07:00","19:00",">7.5t on motorways, trunk roads and Class 1 roads.")
        elif country == "Slovenia":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"08:00","22:00",">7.5t on affected road sections.")
            summer_start = last_weekday(d.year,6,5); summer_end = date(d.year,9,7)
            if summer_start <= d <= summer_end and d.weekday() == 5: add(E,country,"HGV ban — summer Saturday",d,"08:00","13:00",">7.5t on affected road sections; some listed routes have 06:00–16:00 restrictions.")
        elif country == "Switzerland":
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","24:00",">3.5t HGVs and specified combinations; cantonal holiday rules and exemptions apply.")
        elif country == "Romania":
            if h: add(E,country,"HGV ban — public holiday",d,"06:00","22:00",">7.5t on specified national-road sections; route-specific rules apply.")
            if date(d.year,7,1) <= d <= date(d.year,8,31):
                if d.weekday() == 4: add(E,country,"HGV ban — summer Friday",d,"18:00","22:00","Route-specific summer restrictions on affected national roads.")
                if d.weekday() == 5: add(E,country,"HGV ban — summer Saturday",d,"06:00","22:00","Route-specific summer restrictions on affected national roads.")
                if d.weekday() == 6: add(E,country,"HGV ban — summer Sunday",d,"06:00","22:00","Route-specific summer restrictions on affected national roads.")
        d += timedelta(days=1)

    if country == "Italy":
        # 2026 national calendar, based on Italian MIT Decree 325/2025.
        fixed = [
            ("08-14","16:00","22:00"),("08-15","07:00","22:00"),("08-16","07:00","22:00"),
            ("08-22","08:00","16:00"),("08-23","07:00","22:00"),("08-29","08:00","16:00"),
            ("08-30","07:00","22:00"),("09-06","07:00","22:00"),("09-13","07:00","22:00"),
            ("09-20","07:00","22:00"),("09-27","07:00","22:00"),("10-04","09:00","22:00"),
            ("10-11","09:00","22:00"),("10-18","09:00","22:00"),("10-25","09:00","22:00"),
            ("11-01","09:00","22:00"),("11-08","09:00","22:00"),("11-15","09:00","22:00"),
            ("11-22","09:00","22:00"),("11-29","09:00","22:00"),("12-06","09:00","22:00"),
            ("12-08","09:00","22:00"),("12-13","09:00","22:00"),("12-20","09:00","22:00"),
            ("12-25","09:00","22:00"),("12-26","09:00","22:00"),("12-27","09:00","22:00")]
        for md, st, en in fixed:
            m, day = map(int, md.split("-")); add(E,country,"HGV ban — 2026 national restriction",date(2026,m,day),st,en,">7.5t on extra-urban roads; statutory exemptions and route-specific rules apply. 2026 Italian national calendar.")
    return E


def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def make_ics(events):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    desc = ("Discrete TruckBAN HGV restrictions from today onward. " + STANDING_RULES +
            " Always check the country/route source and exemptions before dispatch.")
    L = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//TruckBAN Calendar//EN","CALSCALE:GREGORIAN","METHOD:PUBLISH",
         "X-WR-CALNAME:TruckBAN HGV Restrictions","X-WR-CALDESC:" + esc(desc)]
    for i,(a,b,c,t,d) in enumerate(sorted(events, key=lambda x: x[0])):
        au, bu = a.astimezone(timezone.utc), b.astimezone(timezone.utc)
        L += ["BEGIN:VEVENT",f"UID:{c.replace(' ','-')}-{au.strftime('%Y%m%d%H%M')}-{i}@truckban-calendar",
              f"DTSTAMP:{stamp}",f"DTSTART:{au.strftime('%Y%m%dT%H%M%SZ')}",f"DTEND:{bu.strftime('%Y%m%dT%H%M%SZ')}",
              f"SUMMARY:{esc(c+' — '+t)}",f"DESCRIPTION:{esc(d)}","STATUS:CONFIRMED","END:VEVENT"]
    L.append("END:VCALENDAR"); return "\r\n".join(L)+"\r\n"


def main():
    countries = load_countries(); today = datetime.now(timezone.utc).date(); stop = date(today.year + 1, 12, 31)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True); PUBLIC_DIR.mkdir(parents=True, exist_ok=True); ok = 0
    for country in countries:
        try:
            html = download_page(BASE_URL + country.replace(" ", "%20")); safe = country.replace("/","-").replace("\\","-").replace(" ","_")
            (DEBUG_DIR/f"{safe}.html").write_text(html,encoding="utf-8"); (DEBUG_DIR/f"{safe}.txt").write_text(html_to_text(html),encoding="utf-8"); ok += 1
        except Exception as e: print(f"{country}: FAILED {e}")
    events = []
    for c in sorted(SUPPORTED): events.extend(country_events(c, today, stop))
    (PUBLIC_DIR/"truckban.ics").write_text(make_ics(events),encoding="utf-8")
    (PUBLIC_DIR/"index.html").write_text('<!doctype html><html><head><meta charset="utf-8"><title>TruckBAN Calendar</title></head><body><h1>TruckBAN HGV Restrictions</h1><p><a href="truckban.ics">truckban.ics</a></p><p>Discrete dated restrictions are published; standing daily/night restrictions are described in the calendar description to avoid flooding Outlook.</p></body></html>',encoding="utf-8")
    print(f"Fetched {ok}/{len(countries)} source pages; generated {len(events)} discrete events for {len(SUPPORTED)} countries.")

if __name__ == "__main__": main()
