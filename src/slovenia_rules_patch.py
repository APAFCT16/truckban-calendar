from pathlib import Path

# This patch is intentionally idempotent: the workflow applies it after checkout
# on every run. Slovenia's base generator already contains the correct national
# rules and tourist-season cutoff; this patch only supplies the Romania seasonal
# additions and the two country-feed descriptions.

GENERATOR = Path("src/calendar_generator.py")
COUNTRY_FEEDS = Path("src/country_feeds.py")


def patch_romania_generator():
    s = GENERATOR.read_text(encoding="utf-8")
    start = s.index('        elif country == "Romania":')
    end = s.index('        d += timedelta(days=1)', start)

    new = '''        elif country == "Romania":
            # Romania is route-specific. The recurring national feed represents
            # only the four road sectors listed in Annex 1 to Order 1249/132/2018:
            # A2, DN7, DN39 and DN22C. Direction is material on A2 and DN22C.
            apr_sep = date(d.year, 4, 1) <= d <= date(d.year, 9, 30)
            jul_aug = date(d.year, 7, 1) <= d <= date(d.year, 8, 31)

            if apr_sep:
                if h:
                    add(E,country,"HGV ban — A2 — public holiday — both directions",d,"06:00","22:00",">7.5t; A2 București (DNCB)–Fundulea–Lehliu–Fetești–Cernavodă–Constanța (A4), both directions; statutory exemptions apply.")
                    add(E,country,"HGV ban — DN39 — public holiday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea (DN39A)–Mangalia, both directions; statutory exemptions apply.")
                if d.weekday() == 6:
                    add(E,country,"HGV ban — DN7 — Sunday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; Sunday restriction.")
                    add(E,country,"HGV ban — DN39 — Sunday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; Sunday restriction.")
                    add(E,country,"HGV ban — A2 — Sunday — both directions",d,"06:00","22:00",">7.5t; A2 București–Constanța, both directions; Sunday restriction.")

                # Summer Friday restrictions, 1 July-31 August:
                # A2 București→Constanța: 12:00-22:00 local (09:00-19:00 UTC).
                # DN7 both directions: 18:00-22:00 local (15:00-19:00 UTC).
                # DN39 both directions: 06:00-22:00 local (03:00-19:00 UTC).
                if d.weekday() == 4 and jul_aug:
                    add(E,country,"HGV ban — A2 — summer Friday — București→Constanța",d,"12:00","22:00",">7.5t; A2 București→Constanța, summer Friday restriction 1 July–31 August under Order 1249/132/2018.")
                    add(E,country,"HGV ban — DN7 — summer Friday — both directions",d,"18:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer Friday restriction 1 July–31 August under Order 1249/132/2018.")
                    add(E,country,"HGV ban — DN39 — summer Friday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer Friday restriction 1 July–31 August under Order 1249/132/2018.")

                if d.weekday() == 5 and jul_aug:
                    add(E,country,"HGV ban — A2 — summer Saturday — București→Constanța",d,"06:00","22:00",">7.5t; A2 București→Constanța, summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN7 — summer Saturday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN39 — summer Saturday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer restriction 1 July–31 August.")
                if d.weekday() == 6 and jul_aug:
                    add(E,country,"HGV ban — A2 — summer Sunday — Constanța→București",d,"06:00","22:00",">7.5t; A2 Constanța→București, summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN7 — summer Sunday — both directions",d,"06:00","22:00",">7.5t; DN7 Pitești–Râmnicu Vâlcea–Veștem, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN39 — summer Sunday — both directions",d,"06:00","22:00",">7.5t; DN39 Agigea–Mangalia, both directions; summer restriction 1 July–31 August.")
                    add(E,country,"HGV ban — DN22C — summer Sunday — Murfatlar→Cernavodă",d,"06:00","22:00",">7.5t; DN22C Murfatlar (DN3)→Cernavodă (A2), summer restriction 1 July–31 August; statutory exemptions apply.")
                elif d.weekday() == 0 and jul_aug:
                    add(E,country,"HGV ban — A2 — summer Monday — Constanța→București",d,"12:00","22:00",">7.5t; A2 Constanța→București, summer restriction 1 July–31 August; statutory exemptions apply.")
'''
    GENERATOR.write_text(s[:start] + new + s[end:], encoding="utf-8")


def patch_country_feed_descriptions():
    descriptions = {
        "Slovenia": (
            "Slovenia: HGVs over 7.5t are restricted Sundays and public holidays 08:00-22:00, "
            "with Good Friday 14:00-22:00. During the tourist season (last weekend of June through "
            "first weekend of September), Saturdays are restricted 08:00-13:00 generally, with "
            "06:00-16:00 on A1-E61/70 Ljubljana-Koper-Ljubljana, A3-E70 Divača-Fernetiči, "
            "H5-E751 Škofije-Koper, G1-11 Koper-Dragonja and G1-6 Postojna-Jelšane. "
            "Statutory exemptions and route-specific rules apply; this feed represents the recurring "
            "national framework only."
        ),
        "Romania": (
            "Romania: route-specific HGV restrictions apply to vehicles over 7.5t on four named road sectors under "
            "Order 1249/132/2018: A2 București–Constanța, DN7 Pitești–Râmnicu Vâlcea–Veștem, DN39 Agigea–Mangalia "
            "and DN22C Murfatlar–Cernavodă. A2 and DN39 have public-holiday restrictions from 1 April to 30 September; "
            "DN7 is restricted on public holidays and their eves year-round. From 1 July to 31 August, additional "
            "tourist-season restrictions apply by route and direction: A2 Friday/Saturday București→Constanța and "
            "Sunday/Monday Constanța→București, DN7 Friday-Sunday both directions, DN39 Friday-Sunday both directions, "
            "and DN22C Sunday Murfatlar→Cernavodă. Statutory exemptions and temporary road-specific measures apply; "
            "this feed represents the recurring national route-restriction calendar only."
        ),
    }
    f = COUNTRY_FEEDS.read_text(encoding="utf-8")
    lines = f.splitlines()
    for country, description in descriptions.items():
        replacement = f'    "{country}": "{description}",'
        for i, line in enumerate(lines):
            if line.lstrip().startswith(f'"{country}":'):
                lines[i] = replacement
                break
        else:
            insert_at = next((i for i, line in enumerate(lines) if line.lstrip().startswith('"Croatia":')), None)
            if insert_at is None:
                raise RuntimeError(f"Could not find a safe insertion point for {country} country description")
            lines.insert(insert_at, replacement)
    COUNTRY_FEEDS.write_text("\n".join(lines) + "\n", encoding="utf-8")


patch_romania_generator()
patch_country_feed_descriptions()
print("Applied verified Romanian summer rules and Slovenia/Romania feed descriptions safely.")
