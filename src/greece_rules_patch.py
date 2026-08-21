from pathlib import Path

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")

GREECE_TZ = '    "Greece": "Europe/Athens",\n'
GREECE_DESC = ('    "Greece": "Greece: recurring HGV restrictions apply to vehicles over 3.5t on specified national highways and motorways. The main summer-period rule restricts the outbound direction every Friday 16:00-21:00 and the inbound direction every Sunday 15:00-22:00, on the Athens–Patras, Athens–Thessaloniki, Thessaloniki–N. Moudania, A11 Schimatari–Chalkida, Thessaloniki–Kavala, A5 Ionian, A7 Central Peloponnese and A71 Lefktro–Sparti corridors, plus specified connecting national roads. Additional seasonal route-specific restrictions apply in July/August on the Ioannina–Arta–Antirrio corridor. Greek holiday-period bans are issued by the Hellenic Police and can change by date, route and direction; this recurring feed represents the standing seasonal framework and is not a substitute for the latest temporary holiday order. Statutory exemptions apply.",\n')


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

    if '"Greece": "Europe/Athens"' not in text:
        marker = 'TZ = {\n'
        if marker not in text:
            raise SystemExit("Could not locate timezone dictionary for Greece patch")
        text = text.replace(marker, marker + GREECE_TZ, 1)

    if 'SUPPORTED.add("Greece")' not in text:
        marker = "SUPPORTED = set(TZ)"
        if marker not in text:
            raise SystemExit("Could not locate SUPPORTED set for Greece patch")
        text = text.replace(marker, marker + '\nSUPPORTED.add("Greece")', 1)

    if 'elif country == "Greece":' not in text:
        marker = '        elif country == "Hungary":'
        if marker not in text:
            raise SystemExit("Could not locate Hungary branch for Greece patch")

        branch = '''        elif country == "Greece":
            # Recurring summer framework documented by the Hellenic Police and
            # TruckBAN: >3.5t on specified corridors, outbound Fridays and
            # inbound Sundays. Temporary holiday orders are intentionally kept
            # separate because their dates/routes can change annually.
            routes_out = (
                "A8 Athens–Patras (Elefsina–Rio); "
                "A1 Athens–Thessaloniki–Evzoni (Agios Stefanos–Bralos, "
                "Roditsa–Raches and Makrichori–Leptokarya); "
                "Thessaloniki–N. Moudania toward Chalkidiki; "
                "A11 Schimatari–Chalkida toward Chalkida; "
                "Thessaloniki–Kavala toward Kavala; "
                "A5 Ionian Road toward Ioannina; "
                "A7 Central Peloponnese toward Kalamata; "
                "A71 Lefktro–Sparti toward Sparti; "
                "Ioannina–Arta–Antirrio toward Antirrio; "
                "Thessaloniki–Polygyros EO16 toward Polygyros."
            )
            routes_in = (
                "A8 Athens–Patras toward Athens; "
                "A1 Athens–Thessaloniki–Evzoni toward Athens; "
                "N. Moudania–Thessaloniki toward Thessaloniki; "
                "A11 Schimatari–Chalkida toward Schimatari; "
                "Kavala–Thessaloniki toward Thessaloniki; "
                "A5 Ionian Road toward Rio; "
                "A7 Central Peloponnese toward Athens; "
                "A71 Lefktro–Sparti toward Lefktro; "
                "Ioannina–Arta–Antirrio toward Ioannina; "
                "Thessaloniki–Polygyros EO16 toward Thessaloniki."
            )
            scope = ">3.5t; specified national highways/motorways and directions only; statutory exemptions apply."

            # The recurring summer restriction runs from mid-June to
            # mid-September in the established national framework.
            if date(d.year, 6, 15) <= d <= date(d.year, 9, 15):
                if d.weekday() == 4:
                    add(E, country, "HGV ban — summer Friday outbound", d, "16:00", "21:00", scope + " Outbound direction from major centres. Routes: " + routes_out)
                if d.weekday() == 6:
                    add(E, country, "HGV ban — summer Sunday inbound", d, "15:00", "22:00", scope + " Inbound direction towards major centres. Routes: " + routes_in)

            # Additional July/August restriction on the Ioannina–Arta–Antirrio
            # national road, both directions, as part of the recurring summer
            # traffic-management framework.
            if date(d.year, 7, 1) <= d <= date(d.year, 8, 31):
                ionian_scope = ">3.5t heavy vehicles on both directions of the Ioannina–Arta–Antirrio National Road, approximately km 14 to km 39.4 (Ionian Road junction/Avgo Ioanninon to Kouklisi). Statutory exemptions apply."
                if d.weekday() == 4:
                    add(E, country, "HGV ban — Ioannina–Arta–Antirrio summer Friday", d, "15:00", "22:00", ionian_scope)
                if d.weekday() in (5, 6):
                    add(E, country, "HGV ban — Ioannina–Arta–Antirrio summer weekend", d, "08:00", "22:00", ionian_scope)
'''
        text = text.replace(marker, branch + marker, 1)

    GEN.write_text(text, encoding="utf-8")


def patch_description():
    text = FEEDS.read_text(encoding="utf-8")
    marker = '    "Portugal": '
    if marker not in text:
        raise SystemExit("Could not locate Portugal feed description")

    if '    "Greece": ' in text:
        import re
        text = re.sub(r'    "Greece": ".*?",\n', '', text, count=1)

    text = text.replace(marker, GREECE_DESC + marker, 1)
    FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_description()
    print("Applied Greece recurring HGV restriction rules")
