from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import json


COUNTRIES_FILE = Path("countries.json")
OUTPUT_DIR = Path("debug/truckban")

BASE_URL = "https://truckban.eu/"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        text = " ".join(data.split())
        if text:
            self.parts.append(text)

    def get_text(self):
        return "\n".join(self.parts)


def load_countries():
    with COUNTRIES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)["countries"]


def country_url(country):
    return BASE_URL + country.replace(" ", "%20")


def download_page(url):
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0 Safari/537.36"
            )
        },
    )

    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def html_to_text(html):
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text()


def main():
    countries = load_countries()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    successful = 0
    failed = 0

    print(f"Collecting {len(countries)} TruckBAN country pages.")

    for country in countries:
        print(f"\nChecking {country}...")

        try:
            url = country_url(country)
            html = download_page(url)
            text = html_to_text(html)

            safe_name = (
                country
                .replace("/", "-")
                .replace("\\", "-")
                .replace(" ", "_")
            )

            # Save the original HTML.
            html_file = OUTPUT_DIR / f"{safe_name}.html"
            html_file.write_text(html, encoding="utf-8")

            # Save readable text as well.
            text_file = OUTPUT_DIR / f"{safe_name}.txt"
            text_file.write_text(text, encoding="utf-8")

            successful += 1

            print(
                f"{country}: saved "
                f"{len(html):,} HTML characters / "
                f"{len(text):,} text characters"
            )

        except Exception as error:
            failed += 1
            print(
                f"{country}: FAILED - "
                f"{type(error).__name__}: {error}"
            )

    print("\n------------------------------")
    print(f"Successful countries: {successful}")
    print(f"Failed countries:     {failed}")
    print("------------------------------")
    print(f"Files saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
