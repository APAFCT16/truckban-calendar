from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import re

for p in Path('public').rglob('*.ics'):
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines()
    out = []

    def convert(value, tz):
        dt = datetime.strptime(value, '%Y%m%dT%H%M%S').replace(tzinfo=ZoneInfo(tz))
        return dt.astimezone(ZoneInfo('UTC')).strftime('%Y%m%dT%H%M%SZ')

    for line in lines:
        m = re.match(r'DTSTART;TZID=([^:;]+):(\d{8}T\d{6})$', line)
        if m:
            out.append('DTSTART:' + convert(m.group(2), m.group(1)))
            continue
        m = re.match(r'DTEND;TZID=([^:;]+):(\d{8}T\d{6})$', line)
        if m:
            out.append('DTEND:' + convert(m.group(2), m.group(1)))
            continue
        out.append(line)

    p.write_text('\r\n'.join(out) + '\r\n', encoding='utf-8')
    print(f'Converted {p} to UTC for Classic Outlook compatibility.')
