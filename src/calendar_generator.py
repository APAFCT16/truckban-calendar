from pathlib import Path
from urllib.request import Request, urlopen

print("TRUCKBAN TEST VERSION 2")

URL = "https://truckban.eu/Germany"


def main():
    print(f"Testing access to: {URL}")

    request = Request(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0 Safari/537.36"
            )
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            content = response.read().decode("utf-8", errors="replace")

        print("HTTP request succeeded.")
        print(f"Downloaded {len(content):,} characters.")

        Path("truckban_test.html").write_text(
            content,
            encoding="utf-8",
        )

        print("TruckBAN test page saved successfully.")

        if "Please wait while your request is being verified" in content:
            print("WARNING: TruckBAN returned a verification page.")
        elif "Germany" in content:
            print("SUCCESS: Germany page appears to be accessible.")
        else:
            print("WARNING: Page downloaded but expected content was not found.")

    except Exception as error:
        print("FAILED TO ACCESS TRUCKBAN")
        print(type(error).__name__)
        print(str(error))
        raise


if __name__ == "__main__":
    main()
