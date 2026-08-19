from pathlib import Path
import re

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

    # Portugal uses mainland Europe/Lisbon local time; the normal calendar
    # pipeline converts these local restrictions to UTC for publication.
    text = re.sub(
        r'("Poland"\s*:\s*"Europe/Warsaw",\s*)("Romania"\s*:\s*"Europe/Bucharest",)',
        r'\1"Portugal": "Europe/Lisbon", \2',
        text,
        count=1,
    )

    # Add Portugal to the holidays package country-code map. The source uses
    # whitespace/newlines between entries, so use a whitespace-tolerant regex.
    text = re.sub(
        r'("Romania"\s*:\s*"RO",)',
        r'"Portugal": "PT", \1',
        text,
        count=1,
    )

    # The country-specific Portugal branch is inserted before Romania so the
    # recurring country-event generator can produce the feed without changing
    # the main generator source file permanently.
    if 'elif country == "Portugal":' not in text:
        marker = '        elif country == "Romania":'
        if marker not in text:
            raise SystemExit("Could not locate Romania branch for Portugal patch")

        portugal = '''        elif country == "Portugal":
            # Portugal has no general nationwide Sunday/public-holiday HGV ban
            # for ordinary freight. The recurring national restrictions below
            # are the restrictions applicable to dangerous-goods vehicles under
            # Portaria 281/2019, plus the new VCI Porto rule entering force on
            # 15 September 2026.
            #
            # Important scope distinction: the listed-road, Monday-access and
            # Ponte 25 de Abril restrictions cover heavy dangerous-goods vehicles
            # required to display an orange ADR panel. Tankers are a separate
            # covered class and must be retained in the listed-road Friday/eve
            # rule as well as their nationwide Sunday/holiday rule.
            dangerous_scope = "Heavy vehicles carrying dangerous goods and required to display an orange ADR panel; statutory exemptions apply."
            tanker_scope = "Heavy vehicles carrying dangerous goods in tankers; statutory exemptions apply."
            listed_scope = "Heavy vehicles carrying dangerous goods covered by Portaria 281/2019, including tankers on Fridays and holiday eves."

            # Portaria 281/2019, Art. 2 as amended by Portaria 163/2021:
            # tankers are prohibited nationwide on Sundays and national
            # holidays, except when the holiday falls on Saturday or Monday.
            if (d.weekday() == 6) or (h and d.weekday() not in (0, 5)):
                add(E,country,"HGV ban — dangerous goods — Sunday/public holiday",d,"00:00","24:00",tanker_scope + " Nationwide mainland Portugal; Portaria 281/2019 Art. 2.")

            # Art. 3: covered dangerous-goods vehicles on the complete listed
            # road set, Fridays/Sundays/public holidays/eves 18:00-21:00.
            # Tankers are expressly included on Fridays and holiday eves.
            listed = (
                "EN6 Lisbon–Cascais; EN10 Infantado–Vila Franca de Xira; "
                "EN14 Maia–Braga; EN15 Porto–Campo (A4); EN105 Porto–Alfena (IC24); "
                "IC1 Coimbrões–Miramar; EN209 Porto–Gondomar; EN209 (ER) Gondomar–Valongo; "
                "IC2 (EN1) Alenquer–Carvalhos; EN13 Porto–Viana do Castelo; "
                "EN1 Carvalhos–Vila Nova de Gaia (Santo Ovídio); EN101 Braga–Vila Verde; "
                "EN125 (ER) Lagos–São João da Venda; IC4 (EN125) São João da Venda–Faro; "
                "EN125 Faro–Olhão; EN125 (ER) Olhão–Pinheira junction; EN222 Porto–Crestuma/Lever toll barrier"
            )
            holiday_eve = (d + timedelta(days=1)) in hol
            if d.weekday() == 4 or d.weekday() == 6 or h or holiday_eve:
                scope = listed_scope + " Listed roads: " + listed + "."
                if d.weekday() == 6 or h:
                    scope = dangerous_scope + " " + scope
                add(E,country,"HGV ban — dangerous goods — listed roads",d,"18:00","21:00",scope + " Applies on Fridays, Sundays, national holidays and eves of national holidays; Art. 3.")

            # Art. 4: Monday 07:00-10:00 inbound restrictions on specified
            # Lisbon/Porto access roads, except July and August.
            if d.weekday() == 0 and not (date(d.year,7,1) <= d <= date(d.year,8,31)):
                access = (
                    "A1 Alverca–Lisbon; A5 CREL–Lisbon; A8 Loures–Lisbon; "
                    "IC19 CREL–Lisbon (Damaia); EN6 Cascais–Lisbon; EN10 Vila Franca de Xira–Alverca; "
                    "IC22 A9–Odivelas; A3 IC24–Porto; A4 A3–Matosinhos; A28 Ponte da Arrábida–A4; "
                    "EN13 Moreira–Porto; EN209 Gondomar–Porto; EN222 Avintes–Porto; A20 Ponte do Freixo–A3"
                )
                add(E,country,"HGV ban — dangerous goods — Monday city access",d,"07:00","10:00",dangerous_scope + " Inbound towards Lisbon or Porto on: " + access + ". Art. 4; no restriction in July/August.")

            # Art. 5: dangerous-goods vehicles may use the 25 de Abril Bridge
            # and north viaduct only from 02:00-05:00 every day. The prohibited
            # period is represented as one cross-midnight event (05:00-02:00).
            add(E,country,"HGV ban — dangerous goods — 25 de Abril Bridge",d,"05:00","02:00",dangerous_scope + " Ponte 25 de Abril and north viaduct; passage permitted only 02:00-05:00. Art. 5.")

            # Art. 6(2): dangerous-goods vehicles remain prohibited in the
            # Gardunha Tunnel until a new IMT decision changes that status.
            # The rule is generated for every local Portugal calendar date,
            # including DST transition dates. Publication converts the local
            # event to UTC, so a midnight local event can legitimately have a
            # previous UTC DTSTART and a 25-hour UTC span on the autumn changeover.
            add(E,country,"HGV ban — dangerous goods — Gardunha Tunnel",d,"00:00","24:00",dangerous_scope + " IP2 Gardunha Tunnel, Alpedrinha–Fundão. Prohibition remains in force under Art. 6(2).")

            # New national legislation: from 15 September 2026, qualifying
            # heavy goods vehicles are prohibited on the Porto VCI on weekdays
            # 07:00-21:00. The rule is >3.5t, 3+ axles and first axle height
            # >=1.1m; Porto/Vila Nova de Gaia loading/unloading movements may
            # be habilitated, and other statutory exceptions apply.
            if d >= date(2026,9,15) and d.weekday() < 5:
                add(E,country,"HGV ban — Porto VCI",d,"07:00","21:00",">3.5t, three or more axles, first-axle height >=1.1m; freight vehicles prohibited on the VCI on weekdays. Porto/Vila Nova de Gaia loading/unloading habilitation and statutory exceptions apply. Decree-Law 155-A/2026, effective 15 September 2026.")
'''
        text = text.replace(marker, portugal + marker, 1)

    GEN.write_text(text, encoding="utf-8")


def patch_feed_description():
    text = FEEDS.read_text(encoding="utf-8")
    if '"Portugal": "Portugal:' in text:
        text = re.sub(
            r'    "Portugal": ".*?",\n',
            '    "Portugal": "Portugal: no general nationwide Sunday/public-holiday HGV ban for ordinary freight. This feed represents the recurring national restrictions for dangerous-goods vehicles under Portaria 281/2019 as amended by Portaria 163/2021: tankers are restricted nationwide on Sundays/public holidays and are also covered on Fridays and holiday eves on listed roads; other heavy dangerous-goods vehicles required to display an orange ADR panel are restricted on listed roads and specified Lisbon/Porto access routes. It also includes the Ponte 25 de Abril and Gardunha Tunnel restrictions. From 15 September 2026 it includes the Porto VCI weekday restriction for qualifying heavy goods vehicles over 3.5t, with three or more axles and first-axle height >=1.1m. Statutory exemptions and special authorisations apply; local city restrictions outside these national rules are not automatically represented.",\n',
            text,
            count=1,
        )
        FEEDS.write_text(text, encoding="utf-8")
        return
    marker = 'COUNTRY_DESCRIPTIONS = {\n'
    desc = '''    "Portugal": "Portugal: no general nationwide Sunday/public-holiday HGV ban for ordinary freight. This feed represents the recurring national restrictions for dangerous-goods vehicles under Portaria 281/2019 as amended by Portaria 163/2021: tankers are restricted nationwide on Sundays/public holidays and are also covered on Fridays and holiday eves on listed roads; other heavy dangerous-goods vehicles required to display an orange ADR panel are restricted on listed roads and specified Lisbon/Porto access routes. It also includes the Ponte 25 de Abril and Gardunha Tunnel restrictions. From 15 September 2026 it includes the Porto VCI weekday restriction for qualifying heavy goods vehicles over 3.5t, with three or more axles and first-axle height >=1.1m. Statutory exemptions and special authorisations apply; local city restrictions outside these national rules are not automatically represented."
'''
    if marker not in text:
        raise SystemExit("Could not locate COUNTRY_DESCRIPTIONS")
    text = text.replace(marker, marker + desc, 1)
    FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_feed_description()
    print("Applied verified Portugal dangerous-goods and Porto VCI rules")
