from pathlib import Path
import re

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")

SERBIA_TZ = '    "Serbia": "Europe/Belgrade",\n'
SERBIA_DESC = ('    "Serbia": "Serbia: there is no general nationwide weekend, Sunday or public-holiday HGV driving ban for standard freight traffic. This feed therefore contains no standard nationwide HGV-ban events. Special/abnormal transport, temporary road works, route-specific weight restrictions and other exceptional traffic controls are separate and can be imposed by the competent authorities; check current Roads of Serbia information and permits before dispatch.",\n')


def patch_generator():
    text = GEN.read_text(encoding="utf-8")
    if '"Serbia": "Europe/Belgrade"' not in text:
        marker = '    "Poland": "Europe/Warsaw",'
        if marker not in text:
            raise SystemExit("Could not locate Poland timezone entry")
        text = text.replace(marker, marker + '\n' + SERBIA_TZ.rstrip('\n'), 1)
    if 'elif country == "Serbia":' not in text:
        marker = '        elif country == "Slovakia":'
        if marker not in text:
            raise SystemExit("Could not locate Slovakia branch")
        branch = '''        elif country == "Serbia":
            # Serbia has no general nationwide weekend/public-holiday HGV ban
            # for standard freight traffic. Keep this recurring feed empty;
            # temporary/route-specific and special-transport restrictions are
            # not suitable for a recurring national HGV-ban calendar.
            pass
'''
        text = text.replace(marker, branch + marker, 1)
    GEN.write_text(text, encoding="utf-8")


def patch_description():
    text = FEEDS.read_text(encoding="utf-8")
    text = re.sub(r'    "Serbia": ".*?",\n', '', text, count=1)
    marker = '    "Portugal": '
    if marker not in text:
        raise SystemExit("Could not locate Portugal description")
    text = text.replace(marker, SERBIA_DESC + marker, 1)
    FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_description()
    print("Applied verified Serbia baseline: no general nationwide HGV ban")
