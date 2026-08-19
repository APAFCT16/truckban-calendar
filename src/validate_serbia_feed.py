from pathlib import Path

p = Path("public/countries/Serbia.ics")
if not p.is_file() or p.stat().st_size == 0:
    raise SystemExit("Serbia.ics is missing or empty")

text = p.read_text(encoding="utf-8")
required = [
    "BEGIN:VCALENDAR",
    "END:VCALENDAR",
    "VERSION:2.0",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:TruckBAN — Serbia",
    "X-WR-CALDESC:Serbia: there is no general nationwide weekend, Sunday or public-holiday HGV driving ban",
]
for item in required:
    if item not in text:
        raise SystemExit(f"Missing Serbia feed marker: {item}")

# Serbia has no general nationwide recurring HGV-ban events for standard freight.
# Keep the country feed deliberately empty: no VEVENT means Outlook cannot
# populate the Serbia subscription with invented nationwide restrictions.
if "BEGIN:VEVENT" in text or "Serbia — HGV ban" in text:
    raise SystemExit("Unexpected Serbia HGV-ban event: Serbia baseline should be an empty recurring national feed")

if "DTSTART:" in text or "DTEND:" in text:
    raise SystemExit("Unexpected Serbia event timing: Serbia baseline should contain no events")

if "DTSTART;TZID=" in text or "DTEND;TZID=" in text:
    raise SystemExit("Serbia feed contains timezone-qualified DTSTART/DTEND; Classic Outlook requires UTC")

print("Serbia feed validation passed: valid empty national HGV-ban calendar")
