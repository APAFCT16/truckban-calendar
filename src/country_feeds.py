from datetime import date, datetime, timezone
from pathlib import Path
from calendar_generator import load_countries, country_events, make_ics

PUBLIC_DIR = Path("public")
COUNTRY_DIR = PUBLIC_DIR / "countries"


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
        ).replace(
            "X-WR-CALDESC:Discrete TruckBAN HGV restrictions from today onward. ",
            f"X-WR-CALDESC:TruckBAN restrictions for {country} from today onward. ",
            1,
        )
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
