from __future__ import annotations

from datetime import date, datetime, timezone
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


def assert_window(path: Path, summary: str, tz_name: str, expected_start: str, expected_end: str):
    start, event = first_future(path, summary)
    if event.get("DTEND") != expected_end:
        raise AssertionError(
            f"{path}: {summary}: expected DTEND {expected_end}, got {event.get('DTEND')!r}"
        )
    local = start.astimezone(ZoneInfo(tz_name))
    if local.strftime("%H:%M") != expected_start:
        raise AssertionError(
            f"{path}: {summary}: expected local start {expected_start}, got {local.strftime('%H:%M')}"
        )
    return start.date(), event


def main():
    slovenia = ROOT / "Slovenia.ics"
    sl_start, _ = assert_window(
        slovenia,
        "HGV ban — summer Saturday",
        "Europe/Ljubljana",
        "08:00",
        None,
    )
    # The general Slovenia event is 08:00-13:00 local; verify its UTC end below.
    sl_event = first_future(slovenia, "HGV ban — summer Saturday")[1]
    if sl_event.get("DTEND") != _utc_end(sl_start, "Europe/Ljubljana", "13:00"):
        raise AssertionError("Slovenia general summer Saturday has the wrong end time")

    route_start, route_event = assert_window(
        slovenia,
        "HGV ban — summer Saturday — listed routes",
        "Europe/Ljubljana",
        "06:00",
        _utc_end(sl_start, "Europe/Ljubljana", "16:00"),
    )
    if route_start != sl_start:
        raise AssertionError("Slovenia route-specific and general summer Saturday events are on different dates")

    if sl_start.weekday() != 5:
        raise AssertionError("Slovenia summer Saturday validation found a non-Saturday event")

    greece = ROOT / "Greece.ics"
    fri_date, _ = assert_window(
        greece,
        "HGV ban — summer Friday outbound",
        "Europe/Athens",
        "16:00",
        _utc_end(fri_date_placeholder := date.today(), "Europe/Athens", "21:00"),
    )
    # Recompute the expected end for the actual generated Friday date.
    fri_event = first_future(greece, "HGV ban — summer Friday outbound")[1]
    if fri_event.get("DTEND") != _utc_end(fri_date, "Europe/Athens", "21:00"):
        raise AssertionError("Greece summer Friday outbound has the wrong end time")
    if fri_date.weekday() != 4:
        raise AssertionError("Greece summer Friday validation found a non-Friday event")

    sun_date, sun_event = assert_window(
        greece,
        "HGV ban — summer Sunday inbound",
        "Europe/Athens",
        "15:00",
        _utc_end(first_future(greece, "HGV ban — summer Sunday inbound")[0].date(), "Europe/Athens", "22:00"),
    )
    if sun_date.weekday() != 6:
        raise AssertionError("Greece summer Sunday validation found a non-Sunday event")
    if sun_date <= fri_date:
        raise AssertionError("Greece first future Sunday is not after the first future Friday")

    print(f"Seasonal rolling validation passed: Slovenia Saturday {sl_start}; Greece Friday {fri_date}, Sunday {sun_date}.")


def _utc_end(day: date, tz_name: str, hm: str) -> str:
    h, m = map(int, hm.split(":"))
    local = datetime(day.year, day.month, day.day, h, m, tzinfo=ZoneInfo(tz_name))
    return local.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


if __name__ == "__main__":
    main()
