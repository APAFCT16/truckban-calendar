# Verified Belgium and Luxembourg country-specific rules.
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

    # Luxembourg bans are directional transit bans, not a general Sunday ban.
    # They are triggered by Sundays and by the public holidays of France/Germany,
    # because the legal restriction follows the destination country.
    old_lux = '''        elif country == "Luxembourg":
            if d.weekday() == 5:
                add(E,country,"HGV ban — Saturday towards France",d,"21:30","24:00",">7.5t; direction France.")
                add(E,country,"HGV ban — Saturday towards Germany",d,"23:30","24:00",">7.5t; direction Germany.")
            if d.weekday() == 6 or h: add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","21:45",">7.5t; direction-specific rules and exemptions apply.")
'''
    new_lux = '''        elif country == "Luxembourg":
            fr_holiday = d in holiday_dates("France", years)
            de_holiday = d in holiday_dates("Germany", years)
            next_day = d + timedelta(days=1)
            next_fr_holiday = next_day in holiday_dates("France", years)
            next_de_holiday = next_day in holiday_dates("Germany", years)

            # Every Sunday: affected transit toward France and Germany is banned
            # from 00:00 until 21:45 local time.
            if d.weekday() == 6:
                add(E,country,"HGV ban — Sunday transit towards France",d,"00:00","21:45",">7.5t; transit towards France. Domestic traffic and traffic with a Luxembourg destination are not covered.")
                add(E,country,"HGV ban — Sunday transit towards Germany",d,"00:00","21:45",">7.5t; transit towards Germany. Domestic traffic and traffic with a Luxembourg destination are not covered.")

            # Saturday and the eve of a relevant French/German public holiday.
            if d.weekday() == 5 or next_fr_holiday:
                add(E,country,"HGV ban — transit towards France",d,"21:30","24:00",">7.5t; transit towards France from Belgium/Germany. Applies Saturday evenings and the eve of relevant French public holidays.")
            if d.weekday() == 5 or next_de_holiday:
                add(E,country,"HGV ban — transit towards Germany",d,"23:30","24:00",">7.5t; transit towards Germany from Belgium/France. Applies Saturday evenings and the eve of relevant German public holidays.")

            # Relevant French/German public holiday itself. Do not treat the
            # Luxembourg-only National Day (23 June) as a ban trigger.
            if fr_holiday:
                add(E,country,"HGV ban — public holiday transit towards France",d,"00:00","21:45",">7.5t; transit towards France; French public holiday.")
            if de_holiday:
                add(E,country,"HGV ban — public holiday transit towards Germany",d,"00:00","21:45",">7.5t; transit towards Germany; German public holiday.")
'''
    if old_lux in text:
        text = text.replace(old_lux, new_lux, 1)
    elif 'HGV ban — public holiday transit towards France' not in text:
        raise SystemExit("Could not locate Luxembourg rules block")

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
            )
        if country == "Luxembourg":
            ics = ics.replace(
                "X-WR-CALDESC:TruckBAN restrictions for Luxembourg from today onward. "
                "Standing restrictions not repeated as individual events: Austria night ban 22:00-05:00 for HGVs >7.5t; "
                "Switzerland night ban 22:00-05:00 for HGVs >3.5t; local/route-specific night and environmental restrictions "
                "may also apply. Always check the country/route source and exemptions before dispatch.",
                "X-WR-CALDESC:Luxembourg: >7.5t HGV transit towards France is restricted Saturdays and the eve of relevant French public holidays from 21:30, and on Sundays/public holidays until 21:45. "
                "Transit towards Germany is restricted Saturdays and the eve of relevant German public holidays from 23:30, and on Sundays/public holidays until 21:45. "
                "Domestic traffic, traffic with a Luxembourg destination and transit towards Belgium are not covered by these bans; exemptions apply.",
                1,
            )'''
    if 'if country == "Belgium":' not in text or 'if country == "Luxembourg":' not in text:
        if marker not in text:
            raise SystemExit("Could not locate country feed description block")
        text = text.replace(marker, replacement, 1)
        FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_country_feed_description()
    print("Applied verified Belgium and Luxembourg rules/feed-description patches")
