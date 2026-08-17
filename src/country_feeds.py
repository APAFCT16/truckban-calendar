from datetime import date, datetime, timezone
from pathlib import Path
from calendar_generator import load_countries, country_events, make_ics

PUBLIC_DIR = Path("public")
COUNTRY_DIR = PUBLIC_DIR / "countries"

COUNTRY_DESCRIPTIONS = {
    "Belgium": "Belgium has no general nationwide Sunday/public-holiday or weekend driving ban for standard HGV freight traffic. Exceptional-load, ADR, weather, route and city low-emission-zone restrictions are separate and are not represented as standard HGV ban events.",
    "Luxembourg": "Luxembourg: >7.5t HGV transit towards France is restricted Saturdays and the eve of relevant French public holidays from 21:30, and on Sundays/public holidays until 21:45. Transit towards Germany is restricted Saturdays and the eve of relevant German public holidays from 23:30, and on Sundays/public holidays until 21:45. Domestic traffic, traffic with a Luxembourg destination and transit towards Belgium are not covered by these bans; exemptions apply.",
}


def safe_name(country):
    return country.replace("/", "-").replace("\\", "-").replace(" ", "_")


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
        # Replace the entire generated description line. This avoids inheriting
        # generic country text from make_ics() in country-specific feeds.
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
