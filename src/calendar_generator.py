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

            # Separate standing Sunday restriction on state road D2.
            if d.weekday() == 6:
                add(E,country,"HGV ban — D2 Varaždin–Dubrava Križovljanska",d,"06:00","22:00",">7.5t HGVs, with or without trailer, on state road D2 from Varaždin to GP Dubrava Križovljanska. Local residents/businesses in the D2 zone and specified supply vehicles are exempt under the Croatian order.")
        elif country == "Hungary":
            if d.weekday() == 5:
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
                if d - timedelta(days=1) in hol:
                    add(E,country,"HGV ban — A2 — holiday eve — both directions",d,"16:00","22:00",">7.5t; A2 București (DNCB)–Fundulea–Lehliu–Fetești–Cernavodă–Constanța (A4), both directions; statutory exemptions apply.")
                    add(E,country,"HGV ban — DN39 — holiday eve — both directions",d,"16:00","22:00",">7.5t; DN39 Agigea (DN39A)–Mangalia, both directions; statutory exemptions apply.")

            if h:
                add(E,country,"HGV ban — DN7 — public holiday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești (DN7C)–Râmnicu Vâlcea–Veștem (DN1), both directions; statutory exemptions apply.")
            if d - timedelta(days=1) in hol:
                add(E,country,"HGV ban — DN7 — holiday eve — both directions",d,"18:00","22:00",">7.5t; DN7 Pitești (DN7C)–Râmnicu Vâlcea–Veștem (DN1), both directions; statutory exemptions apply.")

            if jul_aug:
                if d.weekday() == 4:
                    add(E,country,"HGV ban — A2 — summer Friday — București→Constanța",d,"12:00","22:00",">7.5t; A2 București→Constanța, summer restriction 1 July–31 August; statutory exemptions apply.")
                    add(E,country,"HGV ban — DN7 — summer Friday — both directions",d,"18:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN39 — summer Friday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer restriction 1 July–31 August.")
                elif d.weekday() == 5:
                    add(E,country,"HGV ban — A2 — summer Saturday — București→Constanța",d,"06:00","22:00",">7.5t; A2 București→Constanța, summer restriction 1 July–31 August; statutory exemptions apply.")
                    add(E,country,"HGV ban — DN7 — summer Saturday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN39 — summer Saturday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer restriction 1 July–31 August.")
                elif d.weekday() == 6:
                    add(E,country,"HGV ban — A2 — summer Sunday — Constanța→București",d,"06:00","22:00",">7.5t; A2 Constanța→București, summer restriction 1 July–31 August; statutory exemptions apply.")
                    add(E,country,"HGV ban — DN7 — summer Sunday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN39 — summer Sunday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN22C — summer Sunday — Murfatlar→Cernavodă",d,"06:00","22:00",">7.5t; DN22C Murfatlar (DN3)→Cernavodă (A2), summer restriction 1 July–31 August; statutory exemptions apply.")
                elif d.weekday() == 0:
                    add(E,country,"HGV ban — A2 — summer Monday — Constanța→București",d,"12:00","22:00",">7.5t; A2 Constanța→București, summer restriction 1 July–31 August; statutory exemptions apply.")
        d += timedelta(days=1)

    if country == "Italy":
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
    L.append("END:VCALENDAR"); return "\r\n".join(L) + "\r\n"


NOW = datetime.now(timezone.utc)


def fetch_truckban_events(country, today, stop):
    """Best-effort source retrieval for diagnostics; production rules are explicit above."""
    try:
        url = f"{BASE_URL}country/{country.lower().replace(' ', '-')}/"
        text = html_to_text(download_page(url))
        return text[:50000]
    except Exception:
        return ""


def main():
    countries = load_countries()
    today = datetime.now(timezone.utc).date()
    stop = date(today.year + 1, 12, 31)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    events = []
    for country in countries:
        ce = country_events(country, today, stop)
        events.extend(ce)
        (DEBUG_DIR / f"{country.replace(' ', '_')}.txt").write_text(
            "Generated events: " + str(len(ce)) + "\n", encoding="utf-8"
        )
    (PUBLIC_DIR / "truckban.ics").write_text(make_ics(events), encoding="utf-8")
    print(f"Generated {len(events)} events.")


if __name__ == "__main__":
    main()
