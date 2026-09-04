from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path("public/countries")


def events(path: Path):
    text = path.read_text(encoding="utf-8")
    current = None
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            if current is not None:
                out.append(current)
            current = None
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key] = value
    return out


def first_future(path: Path, summary: str):
    now = datetime.now(timezone.utc)
    matches = []
    for event in events(path):
        if event.get("SUMMARY") != summary:
            continue
        value = event.get("DTSTART", "")
        if not value.endswith("Z"):
            raise AssertionError(f"{path}: {summary}: DTSTART is not UTC: {value!r}")
        try:
            start = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise AssertionError(f"{path}: invalid DTSTART {value!r}") from exc
        if start >= now:
            matches.append((start, event))
    if not matches:
        raise AssertionError(f"{path}: no future event found for {summary!r}")
    return min(matches, key=lambda item: item[0])


def utc_at(day, tz_name, hm):
    h, m = map(int, hm.split(":"))
    local = datetime(day.year, day.month, day.day, h, m, tzinfo=ZoneInfo(tz_name))
    return local.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def check_event(path, summary, tz_name, expected_start, expected_end):
    start, event = first_future(path, summary)
    local = start.astimezone(ZoneInfo(tz_name))
    actual_start = local.strftime("%H:%M")
    if actual_start != expected_start:
        raise AssertionError(f"{path}: {summary}: expected local start {expected_start}, got {actual_start}")
    if event.get("DTEND") != utc_at(start.date(), tz_name, expected_end):
        raise AssertionError(
            f"{path}: {summary}: expected DTEND {utc_at(start.date(), tz_name, expected_end)}, "
            f"got {event.get('DTEND')!r}"
        )
    return start.date()


def main():
    slovenia = ROOT / "Slovenia.ics"
    sl_date = check_event(slovenia, "HGV ban — summer Saturday", "Europe/Ljubljana", "08:00", "13:00")
    route_date = check_event(
        slovenia,
        "HGV ban — summer Saturday — listed routes",
        "Europe/Ljubljana",
        "06:00",
        "16:00",
    )
    if sl_date != route_date or sl_date.weekday() != 5:
        raise AssertionError("Slovenia rolling summer Saturday events do not align on the same Saturday")

    greece = ROOT / "Greece.ics"
    fri_date = check_event(
        greece,
        "HGV ban — summer Friday outbound",
        "Europe/Athens",
        "16:00",
        "21:00",
    )
    sun_date = check_event(
        greece,
        "HGV ban — summer Sunday inbound",
        "Europe/Athens",
        "15:00",
        "22:00",
    )
    if fri_date.weekday() != 4 or sun_date.weekday() != 6 or sun_date <= fri_date:
        raise AssertionError("Greece rolling summer Friday/Sunday events are not on the expected weekdays/order")

    print(f"Seasonal rolling validation passed: Slovenia Saturday {sl_date}; Greece Friday {fri_date}, Sunday {sun_date}.")


if __name__ == "__main__":
    main()
