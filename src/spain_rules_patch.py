from pathlib import Path

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

    # Spain is covered by the DGT national traffic-regulation framework, but
    # general-freight restrictions are route/date specific rather than a simple
    # nationwide Sunday/public-holiday ban. Add Spain as a supported country
    # without inventing nationwide events; route-specific DGT restrictions can
    # be added as a separate verified layer.
    text = text.replace(
        '"Slovenia": "Europe/Ljubljana", "Switzerland": "Europe/Zurich",',
        '"Slovenia": "Europe/Ljubljana", "Spain": "Europe/Madrid", "Switzerland": "Europe/Zurich",',
        1,
    )

    text = text.replace(
        '"Romania":"RO","Slovakia":"SK","Slovenia":"SI","Switzerland":"CH"}',
        '"Romania":"RO","Slovakia":"SK","Slovenia":"SI","Spain":"ES","Switzerland":"CH"}',
        1,
    )

    if 'elif country == "Spain":' not in text:
        marker = '        elif country == "Switzerland":'
        if marker not in text:
            raise SystemExit("Could not locate Switzerland branch for Spain patch")
        spain = '''        elif country == "Spain":
            # Spain has no simple nationwide Sunday/public-holiday HGV ban for
            # ordinary freight. DGT restrictions are published by route/date,
            # while Catalonia, the Basque Country and Navarra have separate
            # traffic competences. Keep this baseline feed empty until the
            # route-specific 2026 DGT restrictions are encoded and verified.
            pass
'''
        text = text.replace(marker, spain + marker, 1)

    GEN.write_text(text, encoding="utf-8")


def patch_feed_description():
    text = FEEDS.read_text(encoding="utf-8")
    if '"Spain": "Spain:' in text:
        return
    marker = '    "Romania": "Romania: route-specific HGV restrictions apply'
    idx = text.find(marker)
    if idx == -1:
        raise SystemExit("Could not locate Romania country description")
    # Insert immediately before Romania so the existing descriptions remain unchanged.
    spain = '    "Spain": "Spain: the 2026 DGT national restrictions for general freight vehicles over 7.5t are route- and date-specific rather than a simple nationwide Sunday/public-holiday ban. The national DGT framework excludes Catalonia, the Basque Country and Navarra, which have their own traffic authorities. This baseline Spain feed intentionally contains no nationwide HGV-ban events until the route-specific DGT 2026 restrictions are encoded and verified.",\n'
    text = text[:idx] + spain + text[idx:]
    FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_feed_description()
    print("Added Spain as a supported country with a conservative DGT baseline feed")
