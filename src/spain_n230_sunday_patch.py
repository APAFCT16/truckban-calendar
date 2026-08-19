from pathlib import Path

GEN = Path("src/calendar_generator.py")


def patch_n230_sunday_rule():
    text = GEN.read_text(encoding="utf-8")
    marker = '                if d.month == 6 and d.weekday() == 6:\n'
    if marker not in text:
        raise SystemExit("Could not locate Spain June Sunday branch for N-230 patch")
    if 'N-230 PK 149.2-133.6 / 120.9-119.5 / 116.1-64.1 — Benabarre' in text:
        print("N-230 Sunday rule already present")
        return
    patch = '''                if ((1 <= d.month <= 3) or (d.month == 12 and 6 <= d.day <= 27)) and d.weekday() == 6:\n                    add(E,country,"HGV restriction — N-230 PK 149.2-133.6 / 120.9-119.5 / 116.1-64.1 — Benabarre",d,"13:00","20:00",">7.5t; N-230 named sections, direction Benabarre. 2026 DGT Annex II; Sundays only in the stated periods.")\n'''
    text = text.replace(marker, patch + marker, 1)
    GEN.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_n230_sunday_rule()
    print("Added verified 2026 DGT N-230 Sunday restriction toward Benabarre")
