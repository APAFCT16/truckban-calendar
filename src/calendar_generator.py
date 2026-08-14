from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import json
from zoneinfo import ZoneInfo

COUNTRIES_FILE=Path("countries.json"); DEBUG_DIR=Path("debug/truckban"); PUBLIC_DIR=Path("public")
BASE_URL="https://truckban.eu/"; YEAR=2026; END_YEAR=2027
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139.0 Safari/537.36"
TODAY=date(2026,8,14)

class TextExtractor(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,data):
        text=" ".join(data.split())
        if text:self.parts.append(text)
    def get_text(self): return "\n".join(self.parts)

def load_countries(): return json.loads(COUNTRIES_FILE.read_text(encoding="utf-8"))["countries"]
def download_page(url):
    with urlopen(Request(url,headers={"User-Agent":UA}),timeout=30) as r:return r.read().decode("utf-8",errors="replace")
def html_to_text(html):
    p=TextExtractor();p.feed(html);return p.get_text()
def holiday_dates(country,years):
    try:
        import holidays
        codes={"Austria":"AT","Croatia":"HR","Czech Republic":"CZ","France":"FR","Germany":"DE","Hungary":"HU","Luxembourg":"LU","Poland":"PL","Romania":"RO","Slovakia":"SK","Slovenia":"SI","Switzerland":"CH"}
        code=codes.get(country)
        if not code:return set()
        return {d for y in years for d in holidays.country_holidays(code,years=y).keys()}
    except Exception:return set()

def add(events,country,title,day,st,en,desc,tz):
    def make(hm):
        if hm=="24:00": return datetime(day.year,day.month,day.day,0,0,tzinfo=ZoneInfo(tz))+timedelta(days=1)
        h,m=map(int,hm.split(":"));return datetime(day.year,day.month,day.day,h,m,tzinfo=ZoneInfo(tz))
    a=make(st);b=make(en)
    if b<=a:b+=timedelta(days=1)
    # Only publish events that have not already ended.
    if b.date() < TODAY:return
    events.append((a,b,country,title,desc))

def events_for_country(country):
    tz={"Austria":"Europe/Vienna","Croatia":"Europe/Zagreb","Czech Republic":"Europe/Prague","France":"Europe/Paris","Germany":"Europe/Berlin","Hungary":"Europe/Budapest","Italy":"Europe/Rome","Luxembourg":"Europe/Luxembourg","Poland":"Europe/Warsaw","Romania":"Europe/Bucharest","Slovakia":"Europe/Bratislava","Slovenia":"Europe/Ljubljana","Switzerland":"Europe/Zurich"}.get(country)
    if not tz:return []
    E=[];hol=holiday_dates(country,[YEAR,END_YEAR]);d=TODAY;stop=date(END_YEAR,12,31)
    while d<=stop:
        h=d in hol
        if country=="Germany":
            if d.weekday()==6 or h:add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t and trucks with trailers; nationwide subject to exemptions.",tz)
            if d.weekday()==5 and date(d.year,7,1)<=d<=date(d.year,8,31):add(E,country,"HGV ban — summer Saturday",d,"07:00","20:00",">7.5t/trucks with trailers on specified motorway/federal-road sections.",tz)
        elif country=="Austria":
            if d.weekday()==6 or h:add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00","Weekend/public-holiday restriction; route and exemption rules apply.",tz)
            if d.weekday()==5 and date(d.year,7,1)<=d<=date(d.year,8,31):add(E,country,"HGV ban — summer Saturday",d,"07:00","15:00","Additional summer restriction on specified routes; destination/route conditions apply.",tz)
        elif country=="France":
            if d.weekday()==6 or h:add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t goods vehicles; national restriction.",tz)
            if d.weekday()==5:add(E,country,"HGV ban — Saturday",d,"22:00","24:00",">7.5t goods vehicles; weekend restriction.",tz)
            if d in [date(2026,m,day) for m,day in [(8,15)]]:add(E,country,"HGV ban — Assumption Day",d,"00:00","22:00",">7.5t goods vehicles; public-holiday restriction.",tz)
        elif country=="Czech Republic":
            if d.weekday()==6 or h:add(E,country,"HGV ban — Sunday/public holiday",d,"13:00","22:00",">7.5t on motorways, expressways and relevant first-class roads.",tz)
            if date(d.year,7,1)<=d<=date(d.year,8,31):
                if d.weekday()==4:add(E,country,"HGV ban — summer Friday",d,"17:00","21:00",">7.5t.",tz)
                if d.weekday()==5:add(E,country,"HGV ban — summer Saturday",d,"07:00","13:00",">7.5t.",tz)
        elif country=="Croatia":
            if date(d.year,6,15)<=d<=date(d.year,9,15):
                if d.weekday()==5:add(E,country,"HGV ban — summer Saturday",d,"04:00","14:00",">7.5t or >14m on specified state roads.",tz)
                if d.weekday()==6:add(E,country,"HGV ban — summer Sunday",d,"12:00","23:00",">7.5t or >14m on specified state roads.",tz)
            if h:add(E,country,"HGV ban — public holiday",d,"14:00","23:00",">7.5t or >14m on specified state roads.",tz)
        elif country=="Hungary":
            if d.weekday()==5:add(E,country,"HGV ban — Saturday",d,"15:00" if d.month in (7,8) else "22:00","24:00",">7.5t; summer-period timing applies in July/August.",tz)
            if d.weekday()==6:add(E,country,"HGV ban — Sunday",d,"00:00","22:00",">7.5t; summer-period weekend restriction.",tz)
            if h:add(E,country,"HGV ban — public holiday",d,"00:00","22:00",">7.5t; consecutive-holiday rules may extend restriction.",tz)
        elif country=="Luxembourg":
            if d.weekday()==5:
                add(E,country,"HGV ban — Saturday towards France",d,"21:30","24:00",">7.5t; direction France.",tz);add(E,country,"HGV ban — Saturday towards Germany",d,"23:30","24:00",">7.5t; direction Germany.",tz)
            if d.weekday()==6 or h:add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","21:45",">7.5t; direction-specific rules/exemptions apply.",tz)
        elif country=="Poland":
            summer=date(d.year,6,26)<=d<=date(d.year,8,30)
            if h:add(E,country,"HGV ban — public holiday",d,"08:00","22:00",">12t nationwide.",tz)
            if summer:
                if d.weekday()==4:add(E,country,"HGV ban — summer Friday",d,"18:00","22:00",">12t nationwide.",tz)
                if d.weekday()==5:add(E,country,"HGV ban — summer Saturday",d,"08:00","14:00",">12t nationwide.",tz)
                if d.weekday()==6:add(E,country,"HGV ban — summer Sunday",d,"08:00","22:00",">12t nationwide.",tz)
        elif country=="Slovakia":
            if d.weekday()==6 or h:add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",">7.5t on motorways, trunk and Class 1 roads.",tz)
            if d.weekday()==5 and date(d.year,7,1)<=d<=date(d.year,8,31):add(E,country,"HGV ban — summer Saturday",d,"07:00","19:00",">7.5t on motorways, trunk and Class 1 roads.",tz)
        elif country=="Slovenia":
            if d.weekday()==6 or h:add(E,country,"HGV ban — Sunday/public holiday",d,"08:00","22:00",">7.5t on affected road sections.",tz)
            if d.weekday()==5 and date(d.year,6,25)<=d<=date(d.year,9,7):add(E,country,"HGV ban — summer Saturday",d,"08:00","13:00","Summer restriction; route-specific rules may be longer.",tz)
        elif country=="Switzerland":
            if d.weekday()==6 or h:add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","24:00",">3.5t national Sunday/public-holiday restriction.",tz)
            add(E,country,"Night HGV ban",d,"22:00","24:00","Night traffic restriction.",tz);add(E,country,"Night HGV ban",d+timedelta(days=1),"00:00","05:00","Night traffic restriction.",tz)
        elif country=="Romania":
            if h:add(E,country,"HGV ban — public holiday",d,"06:00","22:00","Specified national roads; route-specific restrictions.",tz)
            if date(d.year,7,1)<=d<=date(d.year,8,31):
                if d.weekday()==4:add(E,country,"HGV ban — summer Friday",d,"18:00","22:00","Route-specific summer restrictions.",tz)
                if d.weekday()==5:add(E,country,"HGV ban — summer Saturday",d,"06:00","22:00","Route-specific summer restrictions.",tz)
                if d.weekday()==6:add(E,country,"HGV ban — summer Sunday",d,"06:00","22:00","Route-specific summer restrictions.",tz)
        d+=timedelta(days=1)
    if country=="Italy":
        fixed=[("08-14","16:00","22:00"),("08-15","07:00","22:00"),("08-16","07:00","22:00"),("08-22","08:00","16:00"),("08-23","07:00","22:00"),("08-29","08:00","16:00"),("08-30","07:00","22:00"),("09-06","07:00","22:00"),("09-13","07:00","22:00"),("09-20","07:00","22:00"),("09-27","07:00","22:00"),("10-04","09:00","22:00"),("10-11","09:00","22:00"),("10-18","09:00","22:00"),("10-25","09:00","22:00"),("11-01","09:00","22:00"),("11-08","09:00","22:00"),("11-15","09:00","22:00"),("11-22","09:00","22:00"),("11-29","09:00","22:00"),("12-06","09:00","22:00"),("12-08","09:00","22:00"),("12-13","09:00","22:00"),("12-20","09:00","22:00"),("12-25","09:00","22:00"),("12-26","09:00","22:00"),("12-27","09:00","22:00")]
        for md,st,en in fixed:
            m,day=map(int,md.split("-"));add(E,country,"HGV ban — 2026 national restriction",date(2026,m,day),st,en,">7.5t on extra-urban roads; statutory exemptions and route-specific rules apply.",tz)
    return E

def esc(s):return s.replace("\\","\\\\").replace(";","\\;").replace(",","\\,").replace("\n","\\n")
def make_ics(events):
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ");L=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//TruckBAN Calendar//EN","CALSCALE:GREGORIAN","METHOD:PUBLISH","X-WR-CALNAME:TruckBAN HGV Restrictions","X-WR-CALDESC:Automatically updated TruckBAN heavy goods vehicle restriction calendar."]
    for i,(a,b,c,t,d) in enumerate(sorted(events)):
        au=a.astimezone(timezone.utc);bu=b.astimezone(timezone.utc)
        L += ["BEGIN:VEVENT",f"UID:{c.replace(' ','-')}-{au.strftime('%Y%m%d%H%M')}-{i}@truckban-calendar",f"DTSTAMP:{stamp}",f"DTSTART:{au.strftime('%Y%m%dT%H%M%SZ')}",f"DTEND:{bu.strftime('%Y%m%dT%H%M%SZ')}",f"SUMMARY:{esc(c+' — '+t)}",f"DESCRIPTION:{esc(d)}","STATUS:CONFIRMED","END:VEVENT"]
    L.append("END:VCALENDAR");return "\r\n".join(L)+"\r\n"

def main():
    countries=load_countries();DEBUG_DIR.mkdir(parents=True,exist_ok=True);PUBLIC_DIR.mkdir(parents=True,exist_ok=True);ok=0
    for country in countries:
        try:
            html=download_page(BASE_URL+country.replace(' ','%20'));safe=country.replace('/','-').replace('\\','-').replace(' ','_');(DEBUG_DIR/f'{safe}.html').write_text(html,encoding='utf-8');(DEBUG_DIR/f'{safe}.txt').write_text(html_to_text(html),encoding='utf-8');ok+=1
        except Exception as e:print(f'{country}: FAILED {e}')
    events=[]
    for c in countries:events.extend(events_for_country(c))
    (PUBLIC_DIR/'truckban.ics').write_text(make_ics(events),encoding='utf-8')
    (PUBLIC_DIR/'index.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>TruckBAN Calendar</title></head><body><h1>TruckBAN HGV Restrictions</h1><p><a href="truckban.ics">truckban.ics</a></p><p>Automatically generated; verify route-specific exemptions before dispatch.</p></body></html>',encoding='utf-8')
    print(f'Fetched {ok}/{len(countries)} countries; generated {len(events)} events.')

if __name__=='__main__':main()
