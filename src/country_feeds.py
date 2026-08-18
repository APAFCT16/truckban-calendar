from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from calendar_generator import load_countries, country_events, make_ics

PUBLIC_DIR = Path("public")
COUNTRY_DIR = PUBLIC_DIR / "countries"

COUNTRY_DESCRIPTIONS = {
    "Austria": "Austria: nationwide weekend and public-holiday HGV bans apply Saturdays 15:00-24:00 and Sundays/public holidays 00:00-22:00. They cover truck/trailer combinations where the truck or trailer exceeds 3.5t, and trucks, articulated vehicles and self-propelled work machines over 7.5t. A separate nationwide night ban applies daily 22:00-05:00 to HGVs over 7.5t, with an exception for qualifying low-noise vehicles carrying the required L-plate/certificate. Additional regional, route-specific and seasonal bans may also apply and are not yet represented in this standard nationwide feed.",
    "Belgium": "Belgium has no general nationwide Sunday/public-holiday or weekend driving ban for standard HGV freight traffic. Exceptional-load, ADR, weather, route and city low-emission-zone restrictions are separate and are not represented as standard HGV ban events.",
    "Luxembourg": "Luxembourg: >7.5t HGV transit towards France is restricted Saturdays and the eve of relevant French public holidays from 21:30, and on Sundays/public holidays until 21:45. Transit towards Germany is restricted Saturdays and the eve of relevant German public holidays from 23:30, and on Sundays/public holidays until 21:45. Domestic traffic, traffic with a Luxembourg destination and transit towards Belgium are not covered by these bans; exemptions apply.",
    "Slovakia": "Slovakia: on motorways, trunk roads and Class 1 roads, HGVs over 7.5t and truck combinations over 3.5t with a trailer/semi-trailer are restricted on Sundays and public holidays. In 2026 the restriction is 00:00-22:00 before 1 September, changing to 06:00-22:00 from 1 September. The summer Saturday restriction (1 July-31 August) is 07:00-19:00 before 1 September; from 1 September the statutory start changes to 09:00. Class III roads have separate permanent restrictions for vehicles over 12t. Exemptions and route-specific rules apply.",
    "Netherlands": "Netherlands: there is no general nationwide weekend, Sunday or public-holiday HGV driving ban. This feed therefore contains no standard nationwide HGV-ban events. Separate local restrictions, zero-emission zones, abnormal-load restrictions and other route-specific controls may apply and are not represented in this standard nationwide feed.",
    "Hungary": "Hungary: nationwide HGV restrictions apply to vehicles over 7.5t. From 1 July to 31 August, the standard restriction runs from Saturday 15:00 to Sunday 22:00; from 1 September to 30 June, it normally runs from the preceding day 22:00 to Sunday/public-holiday 22:00. Public holidays can create longer continuous restriction periods. Statutory exemptions apply, including specific winter exemptions for qualifying international traffic. IMPORTANT: temporary Hungarian government suspensions or partial releases can change a particular date. Check the latest official Hungarian restriction information before dispatch; these temporary changes are not automatically represented in this recurring feed.",
    "Italy": "Italy: the 2026 national HGV restriction calendar applies to goods vehicles over 7.5t on extra-urban roads on the dates and times set by Italian Ministry of Infrastructure and Transport Decree no. 325 of 12 December 2025. Statutory exemptions and special rules apply, including specific arrangements for vehicles arriving from or travelling to abroad, ports and intermodal terminals. This recurring feed represents the national calendar only; regional, route-specific, exceptional-transport and temporary restrictions are not automatically represented. Check the latest Italian official information before dispatch.",
}


def safe_name(country):
    return country.replace("/", "-").replace("\\", "-").replace(" ", "_")


def fix_hungary_feed(ics):
    """Fix Hungary summer weekend end times and add a manual exception-check reminder."""
    lines = ics.splitlines()
    in_hungary_event = False
    in_hungary_summer_event = False
    dtstart = None
    alert = " IMPORTANT: Temporary Hungarian government suspensions or partial releases may change this specific restriction. Check the latest official Hungarian information before dispatch."

    for i, line in enumerate(lines):
        if line.startswith("SUMMARY:Hungary — HGV ban — "):
            in_hungary_event = True
            in_hungary_summer_event = line.startswith("SUMMARY:Hungary — HGV ban — summer weekend")
            dtstart = None
        elif in_hungary_event and line.startswith("DTSTART:"):
            dtstart = datetime.strptime(line[8:], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        elif in_hungary_event and in_hungary_summer_event and line.startswith("DTEND:") and dtstart is not None:
            local_start = dtstart.astimezone(ZoneInfo("Europe/Budapest"))
            local_end = datetime(
                local_start.year, local_start.month, local_start.day,
                22, 0, tzinfo=ZoneInfo("Europe/Budapest")
            ) + timedelta(days=1)
            lines[i] = "DTEND:" + local_end.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        elif in_hungary_event and line.startswith("DESCRIPTION:"):
            if alert not in line:
                lines[i] = line + alert.replace(";", "\\;")
        elif line == "END:VEVENT":
            in_hungary_event = False
            in_hungary_summer_event = False
            dtstart = None
    return "\r\n".join(lines) + "\r\n"


def main():
    countries = load_countries()
    today = datetime.now(timezone.utc).date()
    stop = date(today.year + 1, 12, 31)
    COUNTRY_DIR.mkdir(parents=True, exist_ok=True)

    links = []
    for country in sorted(countries):
        events = country_events(country, today, stop)
        ics = make_ics(events)
        ics = ics.replace(
            "X-WR-CALNAME:TruckBAN HGV Restrictions",
            f"X-WR-CALNAME:TruckBAN — {country}",
            1,
        )
        description = COUNTRY_DESCRIPTIONS.get(
            country,
            f"TruckBAN restrictions for {country} from today onward."
        )
        lines = ics.splitlines()
        replaced = False
        for i, line in enumerate(lines):
            if line.startswith("X-WR-CALDESC:"):
                lines[i] = "X-WR-CALDESC:" + description
                replaced = True
                break
        if not replaced:
            raise RuntimeError(f"Missing X-WR-CALDESC in generated feed for {country}")
        ics = "\r\n".join(lines) + "\r\n"
        if country == "Hungary":
            ics = fix_hungary_feed(ics)
        filename = safe_name(country) + ".ics"
        (COUNTRY_DIR / filename).write_text(ics, encoding="utf-8")
        links.append((country, filename, len(events)))

    rows = "\n".join(
        f'<li><label><input type="checkbox" data-country="{filename}"> {country}</label> — '
        f'<a href="countries/{filename}">{filename}</a> ({count} dated events)</li>'
        for country, filename, count in links
    )
    html = f'''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TruckBAN Calendar — Countries</title>
<style>body{{font-family:system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 20px}}li{{margin:10px 0}}a{{margin-left:8px}}button{{margin:8px 8px 8px 0;padding:8px 12px}}</style>
</head>
<body>
<h1>TruckBAN HGV Restrictions</h1>
<p>Select the countries you want to work with. The checkboxes are a quick selector; Outlook subscriptions themselves can be switched on/off in Outlook's calendar list.</p>
<p><a href="truckban.ics">All countries — combined feed</a></p>
<p><button type="button" onclick="document.querySelectorAll('input').forEach(x=>x.checked=true)">Select all</button>
<button type="button" onclick="document.querySelectorAll('input').forEach(x=>x.checked=false)">Clear all</button></p>
<ul>{rows}</ul>
<script>
document.querySelectorAll('input[data-country]').forEach(box => box.addEventListener('change', () => {{
  const selected = [...document.querySelectorAll('input[data-country]:checked')].map(x => x.dataset.country);
  const params = selected.length ? '?countries=' + encodeURIComponent(selected.join(',')) : '';
  history.replaceState(null, '', location.pathname + params);
}}));
</script>
</body></html>'''
    (PUBLIC_DIR / "countries.html").write_text(html, encoding="utf-8")
    print(f"Generated {len(links)} country-specific ICS feeds in {COUNTRY_DIR}.")


if __name__ == "__main__":
    main()
