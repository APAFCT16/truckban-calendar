from pathlib import Path

GEN = Path("src/calendar_generator.py")
FEEDS = Path("src/country_feeds.py")


def patch_generator():
    text = GEN.read_text(encoding="utf-8")

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
            # DGT 2026 Annex II: Spain has route/date/time-specific HGV
            # restrictions, not a generic nationwide Sunday/public-holiday ban.
            if d.year != 2026:
                pass
            else:
                if ((1 <= d.month <= 3) or (d.month == 12 and 4 <= d.day <= 18)) and d.weekday() == 4:
                    add(E,country,"HGV restriction — N-230 PK 64.1-116.1 / 119.5-120.9 / 133.6-149.2 — France",d,"17:00","24:00",">7.5t; N-230 named sections, direction France. 2026 DGT Annex II.")
                if 6 <= d.month <= 8 and d.weekday() == 5:
                    add(E,country,"HGV restriction — A-49 PK 0-23 — Ayamonte",d,"10:00","14:00",">7.5t; A-49 Camas–Huévar del Aljarafe, direction Ayamonte. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — AP-4 PK 13.5-78 — Cádiz",d,"10:00","13:00",">7.5t; AP-4 Dos Hermanas–Jerez de la Frontera, direction Cádiz. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — N-4 PK 573-627 — Cádiz",d,"10:00","13:00",">7.5t; N-4 Los Palacios y Villafranca–Jerez de la Frontera, direction Cádiz. 2026 DGT Annex II.")
                if 7 <= d.month <= 8 and (d.weekday() in (5, 6) or h):
                    add(E,country,"HGV restriction — A-483 PK 0-41.33 — both directions",d,"11:00","22:00",">7.5t; A-483 Bollullos Par del Condado–Matalascañas, both directions. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-497 PK 0-17.05 — both directions",d,"11:00","22:00",">7.5t; A-497 Huelva–Punta Umbría, both directions. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-5056 PK 0-4.8 — both directions",d,"11:00","22:00",">7.5t; A-5056 Lepe–La Antilla, both directions. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-5076 PK 0-5.4 — both directions",d,"11:00","22:00",">7.5t; A-5076 Lepe (N-431)–La Antilla, both directions. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-370 PK 0-12.16 — both directions",d,"11:00","22:00",">7.5t; A-370 Los Gallardos–Garrucha, both directions. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-8 PK 139.2-169 — Santander",d,"11:00","14:00",">7.5t; A-8 Castro-Urdiales–Laredo, direction Santander. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-8 PK 169-139.2 — Bilbao",d,"16:00","22:00",">7.5t; A-8 Laredo–Castro-Urdiales, direction Bilbao. 2026 DGT Annex II.")
                if d.month == 6 and d.weekday() == 6:
                    add(E,country,"HGV restriction — A-49 PK 76.9-0 — Sevilla",d,"15:00","24:00",">7.5t; A-49 San Juan del Puerto–Camas, direction Sevilla. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — AP-4 PK 78-13.5 — Sevilla",d,"16:00","20:00",">7.5t; AP-4 Jerez de la Frontera–Dos Hermanas, direction Sevilla. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — N-4 PK 627-573 — Sevilla",d,"16:00","20:00",">7.5t; N-4 Jerez de la Frontera–Los Palacios y Villafranca, direction Sevilla. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-45 PK 142-115 — Córdoba",d,"17:00","24:00",">7.5t; A-45 Málaga–Alto Las Pedrizas, direction Córdoba. 2026 DGT Annex II.")
                if date(2026,6,28) <= d <= date(2026,9,6) and (d.weekday() == 6 or h):
                    madrid_routes = [
                        ("A-1", "118.3-11.8", "Boceguillas–Madrid (M-40)", "21:00", "23:00"),
                        ("A-2", "107-10.8", "Mirabueno–Madrid (M-40)", "21:00", "23:00"),
                        ("A-3", "177-6.9", "Atalaya del Cañavate–Madrid (M-40)", "21:00", "23:00"),
                        ("A-5", "75-11.8", "Maqueda–Madrid (M-40)", "21:00", "24:00"),
                        ("A-6", "123-110", "Arévalo–Adanero", "21:00", "23:00"),
                        ("AP-6", "110-60.5", "Adanero–San Rafael", "21:00", "23:00"),
                        ("A-6", "22.3-6.8", "Las Rozas–Madrid", "21:00", "23:00"),
                        ("N-6", "110-42.5", "Adanero–Collado Villalba", "21:00", "23:00"),
                        ("AP-51", "104.8-81.8", "Ávila–Villacastín", "21:00", "23:00"),
                        ("AP-61", "88.55-61.50", "Segovia–San Rafael", "21:00", "23:00"),
                        ("N-110", "246-228", "Berrocalejo Aragona–Villacastín", "21:00", "23:00"),
                        ("N-603", "74.9-64", "Otero de Herreros–San Rafael", "21:00", "23:00"),
                        ("M-501", "59.5-0", "San Martín de Valdeiglesias–Madrid", "21:00", "23:00"),
                    ]
                    for road, pk, section, start, end in madrid_routes:
                        add(E,country,f"HGV restriction — {road} PK {pk} — {section}",d,start,end,f">7.5t; {road} {section}, direction Entry Madrid. 2026 DGT Annex II; applicable Sundays/public holidays only in the stated period.")
                if d == date(2026,4,1):
                    for road, pk, section, start, end, direction in [
                        ("A-6/AP-6","11.65-61.3","Madrid (M-40)–San Rafael","16:00","22:00","Salida Madrid"),
                        ("AP-6/A-6","61.3-182","San Rafael–Tordesillas (A-62)","16:00","22:00","A Coruña"),
                        ("A-1","11.8-50","Madrid (M-40)–Venturada","16:00","22:00","Salida Madrid"),
                        ("A-2","18.3-38.7","Madrid (M-45)–Meco","16:00","22:00","Salida Madrid"),
                        ("A-3","13-80.4","Madrid (M-50)–Tarancón","13:00","22:00","Ambos sentidos"),
                        ("A-4","17.3-120","Madrid (M-50)–Madridejos","13:00","22:00","Salida Madrid"),
                        ("A-5","15.6-106","Madrid (M-50)–Talavera de la Reina","13:00","22:00","Ambos sentidos"),
                        ("A-7","556-575","Santomera–Torres de Cotillas","14:00","21:00","Almería"),
                        ("A-62","113-151","Cabezón de Pisuerga–Tordesillas","16:00","23:00","Frontera Portugal"),
                        ("A-8","139.2-169","Castro-Urdiales–Laredo","17:00","21:00","Santander"),
                    ]:
                        add(E,country,f"HGV restriction — {road} PK {pk} — {section}",d,start,end,f">7.5t; direction {direction}. Specific date: 1 April 2026 (Semana Santa). 2026 DGT Annex II.")
                if d == date(2026,4,2):
                    add(E,country,"HGV restriction — A-6/AP-6 PK 11.65-61.3 — Salida Madrid",d,"07:00","15:00",">7.5t; Madrid (M-40)–San Rafael, direction Salida Madrid. Specific date: 2 April 2026 (Semana Santa). 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-3 PK 13-80.4 — both directions",d,"07:00","15:00",">7.5t; Madrid (M-50)–Tarancón, both directions. Specific date: 2 April 2026 (Semana Santa). 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-62 PK 113-151 — Portugal",d,"08:00","14:00",">7.5t; Cabezón de Pisuerga–Tordesillas, direction Portugal. Specific date: 2 April 2026 (Semana Santa). 2026 DGT Annex II.")
                if d == date(2026,4,3):
                    add(E,country,"HGV restriction — N-230 PK 64.1-116.1 / 119.5-120.9 / 133.6-149.2 — France",d,"08:00","13:00",">7.5t; named N-230 sections, direction France. Specific date: 3 April 2026 (Semana Santa). 2026 DGT Annex II.")
                if d == date(2026,4,5):
                    add(E,country,"HGV restriction — A-3 PK 25-177 — Salida Madrid",d,"13:00","23:00",">7.5t; Arganda–Atalaya del Cañavate, direction Salida Madrid. Specific date: 5 April 2026. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-4 PK 122-6.7 — Entrada Madrid",d,"13:00","23:00",">7.5t; Madridejos–Madrid (M-40), direction Entrada Madrid. Specific date: 5 April 2026. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — A-49 PK 0-50 — Ayamonte",d,"12:00","21:00",">7.5t; Camas–Bollullos Par del Condado, direction Ayamonte. Specific date: 5 April 2026. 2026 DGT Annex II.")
                    add(E,country,"HGV restriction — AP-4 PK 78-13.5 — Sevilla",d,"10:00","13:00",">7.5t; Jerez de la Frontera–Dos Hermanas, direction Sevilla. Specific date: 5 April 2026. 2026 DGT Annex II.")
                if d == date(2026,4,6):
                    add(E,country,"HGV restriction — A-4 PK 17.3-120 — Salida Madrid",d,"07:00","15:00",">7.5t; Madrid (M-50)–Madridejos, direction Salida Madrid. Specific date: 6 April 2026 (Semana Santa). 2026 DGT Annex II.")
'''
        text = text.replace(marker, spain + marker, 1)

    GEN.write_text(text, encoding="utf-8")


def patch_feed_description():
    text = FEEDS.read_text(encoding="utf-8")
    text = text.replace(
        '"Spain": "Spain: the 2026 DGT national restrictions for general freight vehicles over 7.5t are route- and date-specific rather than a simple nationwide Sunday/public-holiday ban. The national DGT framework excludes Catalonia, the Basque Country and Navarra, which have their own traffic authorities. This baseline Spain feed intentionally contains no nationwide HGV-ban events until the route-specific DGT 2026 restrictions are encoded and verified.",',
        '"Spain": "Spain: this feed contains only route-, date-, time- and direction-specific restrictions from the 2026 DGT national traffic regulation (Annex II). It does NOT create a generic nationwide Sunday/public-holiday HGV ban. The DGT national framework excludes Catalonia, the Basque Country and Navarra, which have separate traffic authorities. Restrictions shown are for vehicles over 7.5t and identify the affected road section and direction where specified.",',
        1,
    )
    FEEDS.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_generator()
    patch_feed_description()
    print("Added verified route/date/time/direction-specific Spain 2026 DGT restrictions")
