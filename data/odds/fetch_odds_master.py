import requests
import json
import pandas as pd
import unicodedata
import re
from rapidfuzz.fuzz import partial_token_set_ratio
from datetime import datetime, timedelta
from pathlib import Path

# === CONFIGURATION ===
API_KEY = "849aad70b83e59689a6e6632b0a1855827ce576fa940d8acebcead3ae8eef61a"
BASE_URL = "https://api.api-tennis.com/tennis"
DATE_START = datetime.utcnow().strftime("%Y-%m-%d")
DATE_STOP = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")
MATCH_WINDOW_MINUTES = 75  # 🔄 Increased from 30 to 75

# === FILE PATHS ===
odds_dir = Path("data/odds")
odds_dir.mkdir(parents=True, exist_ok=True)
combined_path = odds_dir / "api_tennis_combined.json"
flat_csv_path = odds_dir / "fixture_odds_flat.csv"
upcoming_path = Path("data/current/matches_upcoming.csv")

# === HELPERS ===
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

def safe_float(val):
    try:
        return float(str(val).replace(",", ".").strip())
    except:
        return None

def best_odds_with_betano_first(odds_dict):
    if "Betano" in odds_dict:
        return safe_float(odds_dict["Betano"])
    return max(
        [safe_float(v) for v in odds_dict.values() if safe_float(v) is not None],
        default=None
    )

def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"\[[^]]]*\]", "", name)
    name = name.lower().strip()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-z0-9\s.]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def parse_time(tstr):
    try:
        return datetime.strptime(str(tstr).strip(), "%H:%M").time()
    except:
        return None

def time_diff_minutes(t1, t2):
    if t1 and t2:
        return abs((datetime.combine(datetime.today(), t1) - datetime.combine(datetime.today(), t2)).total_seconds() / 60)
    return 9999

# === STEP 1: Fetch and save combined JSON ===
fixtures = fetch_data("get_fixtures")
odds = fetch_data("get_odds")
combined = {
    "fetched_at": datetime.utcnow().isoformat(),
    "fixtures": fixtures.get("result", []),
    "odds": odds.get("result", {})
}
combined_path.write_text(json.dumps(combined, indent=2))
print(f"✅ Saved combined file to {combined_path}")

# === STEP 2: Flatten to CSV ===
fixtures = combined["fixtures"]
odds_by_event = combined["odds"]
rows = []
with_odds = 0
for fixture in fixtures:
    event_key = str(fixture.get("event_key", ""))
    event_date = fixture.get("event_date", "")
    event_time = fixture.get("event_time", "")
    player_A = fixture.get("event_first_player", "")
    player_B = fixture.get("event_second_player", "")

    odds_data = odds_by_event.get(event_key, {}).get("Home/Away", {})
    home_odds = odds_data.get("Home", {})
    away_odds = odds_data.get("Away", {})

    odds_A = best_odds_with_betano_first(home_odds)
    odds_B = best_odds_with_betano_first(away_odds)

    if odds_A and odds_B:
        with_odds += 1

    rows.append({
        "event_key": event_key,
        "date": event_date,
        "time": event_time,
        "player_A": player_A,
        "player_B": player_B,
        "odds_A": odds_A,
        "odds_B": odds_B
    })

df = pd.DataFrame(rows)
df.to_csv(flat_csv_path, index=False)
print(f"\n✅ Saved flat odds CSV to {flat_csv_path}")
print(f"📊 Fixture + Odds Summary: {len(df)} total, {with_odds} with odds, {len(df) - with_odds} without")

# === STEP 3: Inject odds into matches_upcoming.csv ===
upcoming_df = pd.read_csv(upcoming_path)
fixture_df = pd.read_csv(flat_csv_path)

matches_updated = 0
no_match_found = 0
matched_but_no_odds = 0
debug_limit = 5
debug_matches = []

for idx, row in upcoming_df.iterrows():
    raw_A = str(row["player_A"])
    raw_B = str(row["player_B"])
    match_date = str(row.get("date", "")).strip()
    match_time = parse_time(row.get("time", ""))

    norm_A = normalize_name(raw_A)
    norm_B = normalize_name(raw_B)

    best_match = None
    best_score = 0

    same_day = fixture_df[fixture_df["date"] == match_date].copy()
    same_day["parsed_time"] = same_day["time"].apply(parse_time)
    same_day = same_day[same_day["parsed_time"].apply(lambda t: time_diff_minutes(t, match_time) <= MATCH_WINDOW_MINUTES)]

    for _, f in same_day.iterrows():
        fA = normalize_name(f["player_A"])
        fB = normalize_name(f["player_B"])

        score1 = (partial_token_set_ratio(norm_A, fA) + partial_token_set_ratio(norm_B, fB)) / 2
        score2 = (partial_token_set_ratio(norm_A, fB) + partial_token_set_ratio(norm_B, fA)) / 2
        score = max(score1, score2)

        tokens_A = set(norm_A.split())
        tokens_B = set(norm_B.split())
        tokens_fixture = set((fA + " " + fB).split())
        common_tokens = (tokens_A | tokens_B) & tokens_fixture
        valid_token_count = len([t for t in common_tokens if len(t) >= 3])

        if score >= 85 and valid_token_count >= 2 and score > best_score:
            best_score = score
            best_match = f

    print(f"\n🔎 Trying match: {raw_A} / {raw_B} on {match_date} at {row.get('time', '')}")
    print(f"    → Best fuzzy score: {round(best_score)}")

    if best_match is not None:
        print(f"✅ Fuzzy match: {best_match['player_A']} / {best_match['player_B']} | Score: {round(best_score)}")
        print(f"   ↪ Odds A: {best_match['odds_A']}, Odds B: {best_match['odds_B']}")

        if pd.notnull(best_match["odds_A"]) and pd.notnull(best_match["odds_B"]):
            upcoming_df.at[idx, "odds_A"] = best_match["odds_A"]
            upcoming_df.at[idx, "odds_B"] = best_match["odds_B"]
            matches_updated += 1
            if debug_limit > 0:
                debug_matches.append({
                    "match_player_A": raw_A,
                    "match_player_B": raw_B,
                    "fixture_A": best_match["player_A"],
                    "fixture_B": best_match["player_B"],
                    "odds_A": best_match["odds_A"],
                    "odds_B": best_match["odds_B"],
                    "score": round(best_score)
                })
                debug_limit -= 1
        else:
            matched_but_no_odds += 1
            print("⚠️  Match found but odds are missing (null values)")
    else:
        no_match_found += 1
        print("❌ No fuzzy match found.")

# Save final output
upcoming_df.to_csv(upcoming_path, index=False)

# === Final Summary ===
total = len(upcoming_df)
print(f"\n📊 Odds Injection Summary:")
print(f"🟡 Total upcoming matches: {total}")
print(f"🟢 Matches updated with odds: {matches_updated}")
print(f"🔴 Matches skipped: {total - matches_updated}")
print(f"   └─ ❌ No fuzzy match found: {no_match_found}")
print(f"   └─ ⚠️  Match found but no odds: {matched_but_no_odds}")

if debug_matches:
    print("\n🔍 Debug Matches (Top 5):")
    for m in debug_matches:
        print(f"  ↪ {m['match_player_A']} / {m['match_player_B']} ←→ {m['fixture_A']} / {m['fixture_B']} | "
              f"Odds A: {m['odds_A']} | Odds B: {m['odds_B']} | Match Score: {m['score']}")
