import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# === CONFIGURATION ===
API_KEY = "849aad70b83e59689a6e6632b0a1855827ce576fa940d8acebcead3ae8eef61a"
BASE_URL = "https://api.api-tennis.com/tennis"
DATE_START = datetime.utcnow().strftime("%Y-%m-%d")
DATE_STOP = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")

# === FILE PATHS ===
odds_dir = Path("data/odds")
odds_dir.mkdir(parents=True, exist_ok=True)

COMBINED_FILE = odds_dir / "api_tennis_combined.json"

# === HELPER ===
def fetch_data(method):
    print(f"🌐 Fetching: {method}")
    params = {
        "method": method,
        "APIkey": API_KEY,
        "date_start": DATE_START,
        "date_stop": DATE_STOP
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed to fetch {method}: {e}")
        return {}

# === MAIN ===
def main():
    fixtures = fetch_data("get_fixtures")
    odds = fetch_data("get_odds")

    combined = {
        "fetched_at": datetime.utcnow().isoformat(),
        "fixtures": fixtures.get("result", []),
        "odds": odds.get("result", {})
    }

    COMBINED_FILE.write_text(json.dumps(combined, indent=2))
    print(f"✅ Saved combined file to {COMBINED_FILE}")

if __name__ == "__main__":
    main()
