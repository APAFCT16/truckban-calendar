from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import re

# Classic Outlook is most reliable with explicit UTC DTSTART/DTEND values.
# Handle the normal DTSTART;TZID=... form as well as parameterised variants,
# so no timezone-bearing DTSTART/DTEND lines can leak into the published feeds.
for p in Path('public').rglob('*.ics'):
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines()
    out = []

    def convert(value, tz):
        dt = datetime.strptime(value, '%Y%m%dT%H%M%S').replace(tzinfo=ZoneInfo(tz))
        return dt.astimezone(ZoneInfo('UTC')).strftime('%Y%m%dT%H%M%SZ')

    for line in lines:
        # Standard form: DTSTART;TZID=Europe/Warsaw:20260821T180000
        m = re.match(r'^(DTSTART|DTEND);TZID=([^:;]+):(\d{8}T\d{6})$', line)
        if m:
            out.append(m.group(1) + ':' + convert(m.group(3), m.group(2)))
            continue

        # Parameterised form: allow additional RFC5545 parameters around TZID.
        m = re.match(r'^(DTSTART|DTEND)(?:;[^:;]+)*;TZID=([^:;]+)(?:;[^:;]+)*:(\d{8}T\d{6})$', line)
        if m:
            out.append(m.group(1) + ':' + convert(m.group(3), m.group(2)))
            continue

        out.append(line)

    p.write_text('\r\n'.join(out) + '\r\n', encoding='utf-8')
    print(f'Converted {p} to UTC for Classic Outlook compatibility.')
