from pathlib import Path

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

    old_tz = '"Austria": "Europe/Vienna", "Croatia": "Europe/Zagreb", "Czech Republic": "Europe/Prague",'
    new_tz = '"Austria": "Europe/Vienna", "Belgium": "Europe/Brussels", "Croatia": "Europe/Zagreb", "Czech Republic": "Europe/Prague",'
    if '"Belgium": "Europe/Brussels"' not in text:
        if old_tz not in text:
            raise SystemExit("Could not locate TZ table for Belgium patch")
        text = text.replace(old_tz, new_tz, 1)

    marker = '        elif country == "Czech Republic":'
    belgium = '''        elif country == "Belgium":
            # Belgium has no general nationwide Sunday/public-holiday or weekend
            # driving ban for standard HGV freight traffic. Keep the feed empty
            # rather than creating misleading calendar events. Exceptional-load,
            # ADR, weather and city/LEZ restrictions are handled separately in the
            # country feed description and are not standard HGV driving bans.
            pass
'''
    if 'elif country == "Belgium":' not in text:
        if marker not in text:
            raise SystemExit("Could not locate country rules insertion point")
        text = text.replace(marker, belgium + marker, 1)

    GEN.write_text(text, encoding="utf-8")


def patch_country_feed_description():
    text = FEEDS.read_text(encoding="utf-8")
    marker = '''        ).replace(
            "X-WR-CALDESC:Discrete TruckBAN HGV restrictions from today onward. ",
            f"X-WR-CALDESC:TruckBAN restrictions for {country} from today onward. ",
            1,
        )'''
    replacement = '''        ).replace(
            "X-WR-CALDESC:Discrete TruckBAN HGV restrictions from today onward. ",
            f"X-WR-CALDESC:TruckBAN restrictions for {country} from today onward. ",
            1,
        )
        if country == "Belgium":
            ics = ics.replace(
                "X-WR-CALDESC:TruckBAN restrictions for Belgium from today onward. "
                "Standing restrictions not repeated as individual events: Austria night ban 22:00-05:00 for HGVs >7.5t; "
                "Switzerland night ban 22:00-05:00 for HGVs >3.5t; local/route-specific night and environmental restrictions "
                "may also apply. Always check the country/route source and exemptions before dispatch.",
                "X-WR-CALDESC:Belgium has no general nationwide Sunday/public-holiday or weekend driving ban for standard HGV freight traffic. "
                "Exceptional-load, ADR, weather, route and city low-emission-zone restrictions are separate and are not represented as standard HGV ban events. "
                "Always check the applicable Belgian route/source and exemptions before dispatch.",
                1,
            )'''
    if 'if country == "Belgium":' not in text:
        if marker not in text:
            raise SystemExit("Could not locate country feed description block")
        text = text.replace(marker, replacement, 1)
        FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_country_feed_description()
    print("Applied Belgium rules/feed-description patch")
