from pathlib import Path

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")
    if 'elif country == "Switzerland":' in text:
        return

    marker = '        elif country == "Slovakia":'
    if marker not in text:
        raise SystemExit("Could not locate Slovakia branch for Switzerland insertion")

    branch = '''        elif country == "Switzerland":
            scope = ">3.5t permissible total weight; articulated motor vehicles over 5t permissible total towing weight; or vehicles towing a trailer over 3.5t permissible total weight. Statutory exemptions apply."
            if d.weekday() == 6 or h:
                add(E,country,"HGV ban — Sunday/public holiday",d,"00:00","22:00",scope)
'''
    text = text.replace(marker, branch + marker, 1)
    GEN.write_text(text, encoding="utf-8")


def patch_feed_description():
    text = FEEDS.read_text(encoding="utf-8")
    if '    "Switzerland": ' in text:
        return

    marker = '    "Portugal": '
    pos = text.find(marker)
    if pos < 0:
        raise SystemExit("Could not locate Portugal description")

    desc = ('    "Switzerland": "Switzerland: a general Sunday and public-holiday driving ban applies to vehicles with a permissible total weight over 3.5t, articulated motor vehicles with a permissible total towing weight over 5t, and vehicles towing a trailer with a permissible total weight over 3.5t. The Sunday/public-holiday ban is 00:00-22:00; a separate nationwide night ban applies every day 22:00-05:00. The driving ban also applies on New Year, Good Friday, Easter Monday, Ascension Day, Whit Monday, 1 August, Christmas Day and 26 December where Christmas does not fall on a Monday or Friday; it does not apply in cantons or parts of cantons where the relevant holiday is not celebrated. Statutory exemptions and special permits apply. This feed represents the recurring nationwide framework; cantonal, route-specific and temporary restrictions are not automatically represented.",\n')
    text = text[:pos] + desc + text[pos:]
    FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_feed_description()
    print("Applied Switzerland Sunday/public-holiday HGV rules")
