from pathlib import Path

GEN = Path("src/calendar_generator.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")
    if 'if country == "Switzerland":\n        # ASTRA identifies only these days' in text:
        return

    marker = '''def holiday_dates(country, years):\n    try:\n        import holidays\n'''
    if marker not in text:
        raise SystemExit("Could not locate holiday_dates() for Switzerland holiday patch")

    insertion = '''def holiday_dates(country, years):\n    if country == "Switzerland":\n        # ASTRA identifies only these days, in addition to every Sunday, as\n        # Swiss HGV-driving-ban public holidays. Do not use the generic\n        # holidays package here because it also exposes cantonal/observance\n        # dates (for example Christmas Eve and New Year's Eve) that are not\n        # part of the nationwide driving-ban list.\n        result = set()\n        for year in years:\n            a = year % 19\n            b = year // 100\n            c = year % 100\n            d = b // 4\n            e = b % 4\n            f = (b + 8) // 25\n            g = (b - f + 1) // 3\n            h = (19 * a + b - d - g + 15) % 30\n            i = c // 4\n            k = c % 4\n            l = (32 + 2 * e + 2 * i - h - k) % 7\n            m = (a + 11 * h + 22 * l) // 451\n            easter_month = (h + l - 7 * m + 114) // 31\n            easter_day = ((h + l - 7 * m + 114) % 31) + 1\n            easter = date(year, easter_month, easter_day)\n            christmas = date(year, 12, 25)\n            result.update({\n                date(year, 1, 1),                 # New Year's Day\n                easter - timedelta(days=2),       # Good Friday\n                easter + timedelta(days=1),       # Easter Monday\n                easter + timedelta(days=39),      # Ascension Day\n                easter + timedelta(days=50),      # Whit Monday\n                date(year, 8, 1),                 # Swiss National Day\n                christmas,\n            })\n            # 26 December applies only where Christmas is not a Monday or Friday.\n            if christmas.weekday() not in (0, 4):\n                result.add(date(year, 12, 26))\n        return result\n\n    try:\n        import holidays\n'''

    text = text.replace(marker, insertion, 1)
    GEN.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    print("Applied verified Switzerland public-holiday driving-ban dates")
