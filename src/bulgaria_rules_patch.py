from pathlib import Path

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

    # Insert Bulgaria into the actual multiline TZ dictionary used by the
    # current generator. The previous patch expected a one-line fragment that
    # no longer exists, causing the build to stop before generation.
    if '"Bulgaria": "Europe/Sofia"' not in text:
        marker = 'TZ = {\n'
        if marker not in text:
            raise SystemExit("Could not locate timezone dictionary for Bulgaria patch")
        text = text.replace(
            marker,
            marker + '    "Bulgaria": "Europe/Sofia",\n',
            1,
        )

    # The generator builds SUPPORTED from TZ at module-load time. Keep an
    # explicit runtime guard as well so Bulgaria cannot accidentally produce
    # an empty feed if the base generator changes its supported-country gate.
    if 'SUPPORTED.add("Bulgaria")' not in text:
        marker = "SUPPORTED = set(TZ)"
        if marker not in text:
            raise SystemExit("Could not locate SUPPORTED set for Bulgaria patch")
        text = text.replace(marker, marker + '\nSUPPORTED.add("Bulgaria")', 1)

    if 'elif country == "Bulgaria":' not in text:
        marker = '        elif country == "Czech Republic":'
        if marker not in text:
            raise SystemExit("Could not locate country branch for Bulgaria patch")
        branch = '''        elif country == "Bulgaria":
            # 2026 temporary holiday-period restrictions announced by the
            # Bulgarian Road Infrastructure Agency. These are route-specific
            # restrictions for HGVs over 12t, not a nationwide all-road ban.
            if d.year == 2026:
                restrictions = {
                    date(2026, 9, 4): ("14:00", "20:00", "holiday eve — Unification Day"),
                    date(2026, 9, 5): ("09:00", "14:00", "holiday-period Saturday — Unification Day"),
                    date(2026, 9, 7): ("12:00", "20:00", "holiday-period return — Unification Day"),
                    date(2026, 9, 18): ("14:00", "20:00", "holiday eve — Independence Day"),
                    date(2026, 9, 22): ("12:00", "20:00", "holiday — Independence Day"),
                    date(2026, 12, 23): ("14:00", "20:00", "holiday eve — Christmas/New Year period"),
                    date(2026, 12, 24): ("09:00", "14:00", "holiday-period day — Christmas/New Year period"),
                    date(2026, 12, 28): ("12:00", "20:00", "holiday-period return — Christmas/New Year period"),
                }
                if d in restrictions:
                    start, end, label = restrictions[d]
                    add(E,country,"HGV restriction — " + label,d,start,end,">12t HGVs on specified sections of the Trakia, Hemus and Struma motorways and the I-1 Simitli–Kresna section, subject to direction, route and statutory exemptions. This is the 2026 Bulgarian holiday-period traffic restriction schedule; it is not a nationwide all-road ban.")
'''
        text = text.replace(marker, branch + marker, 1)

    GEN.write_text(text, encoding="utf-8")


def patch_feed_description():
    text = FEEDS.read_text(encoding="utf-8")
    if '"Bulgaria":' not in text:
        marker = '    "Portugal": '
        pos = text.find(marker)
        if pos < 0:
            raise SystemExit("Could not locate Portugal feed description")
        desc = '    "Bulgaria": "Bulgaria: 2026 temporary holiday-period HGV restrictions for vehicles over 12t apply on specified sections of the Trakia, Hemus and Struma motorways and the I-1 Simitli–Kresna section. This feed records the 2026 Road Infrastructure Agency schedule from 4 September through 28 December; it is not a nationwide all-road ban. Temporary summer and other route-specific restrictions may be announced separately and are not automatically represented. Statutory exemptions apply. Check the latest Bulgarian official information before dispatch.",\n'
        text = text[:pos] + desc + text[pos:]
    FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_feed_description()
    print("Applied verified Bulgaria rules")
