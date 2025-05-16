import requests
import pandas as pd
import hashlib
from rapidfuzz import fuzz
import time
import json
import os

API_KEY = "1341c902d18decb68a43f9b328bd4802"
UPCOMING_CSV = "data/current/matches_upcoming.csv"
ODDS_JSON = "data/odds/oddsapi_response.json"

# 1. Fetch active tennis competitions
def get_active_tennis_keys():
    url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    resp = requests.get(url)
    data = resp.json()
    return [s["key"] for s in data if s["group"] == "Tennis" and s["active"]]

# 2. Fetch odds from OddsAPI for all active tennis comps
def fetch_odds():
    print("\n🌐 Fetching live odds from OddsAPI...")
    odds_all = []
    headers = {"User-Agent": "CapBot Odds Fetcher"}
    for sport_key in get_active_tennis_keys():
        url = (
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
            f"?apiKey={API_KEY}&regions=us,uk,eu&markets=h2h"
        )
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"⚠️ Failed {sport_key}: {resp.status_code} - {resp.text}")
            continue
        odds_all += resp.json()
        time.sleep(1)  # avoid throttling

    os.makedirs(os.path.dirname(ODDS_JSON), exist_ok=True)
    with open(ODDS_JSON, "w") as f:
        json.dump(odds_all, f, indent=2)
    print(f"✅ Fetched and saved → {ODDS_JSON}")
    return odds_all

# 3. Normalize names

def normalize(name):
    return name.lower().replace(" ", "").replace(".", "").replace("-", "")

# 4. Match & inject odds into upcoming matches
def match_and_update(odds_data):
    df = pd.read_csv(UPCOMING_CSV)
    total_matches = len(df)
    updated = 0
    match_log = []

    for match in odds_data:
        home = match.get("home_team")
        away = match.get("away_team")
        outcomes = None

        for book in match.get("bookmakers", []):
            for market in book.get("markets", []):
                if market["key"] == "h2h":
                    outcomes = market.get("outcomes")
                    break
            if outcomes:
                break

        if not outcomes or len(outcomes) != 2:
            continue

        o1 = outcomes[0]
        o2 = outcomes[1]
        name1, name2 = o1["name"], o2["name"]
        odds1, odds2 = o1["price"], o2["price"]

        for i, row in df.iterrows():
            score = (fuzz.ratio(normalize(row["player_A"]), normalize(name1)) +
                     fuzz.ratio(normalize(row["player_B"]), normalize(name2))) / 2

            if score >= 85:
                df.at[i, "odds_A"] = odds1
                df.at[i, "odds_B"] = odds2
                updated += 1
                match_log.append(
                    f"✅ Matched: {row['player_A']} vs {row['player_B']} ↔ {name1} vs {name2} (score={score:.1f})"
                )
                break

    df.to_csv(UPCOMING_CSV, index=False)

    print(f"\n📊 Match Odds Injection Summary:")
    print(f"🟡 Total 'upcoming' matches: {total_matches}")
    print(f"🟢 Matches updated with odds: {updated}")
    if updated == 0:
        print("⚠️ No matches matched or odds found.")
    else:
        print("\n🔍 Match Log:")
        for log in match_log:
            print(log)

# 5. Main pipeline
def main():
    odds_data = fetch_odds()
    match_and_update(odds_data)

if __name__ == "__main__":
    main()
