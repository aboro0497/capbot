#Fully working - get players stats, h2h, standing
import requests
import json
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from difflib import get_close_matches
from rapidfuzz.fuzz import partial_token_set_ratio
import unicodedata

# === CONFIG ===
API_KEY = "849aad70b83e59689a6e6632b0a1855827ce576fa940d8acebcead3ae8eef61a"
BASE_URL = "https://api.api-tennis.com/tennis"

# === PATHS ===
base_dir = Path("data/api-tennis")
json_dir = base_dir / "json"
player_dir = json_dir / "player_cache"
h2h_dir = json_dir / "h2h_cache"
processed_dir = base_dir / "processed"
upcoming_path = Path("data/current/matches_upcoming.csv")
players_path = processed_dir / "players.csv"
standings_path = processed_dir / "standings.csv"

for d in [json_dir, h2h_dir, player_dir, processed_dir]:
    d.mkdir(parents=True, exist_ok=True)

# === HELPERS ===
def fetch_data(method, params=None):
    print(f"🌐 Fetching: {method}")
    payload = {"method": method, "APIkey": API_KEY}
    if params:
        payload.update(params)
    try:
        response = requests.get(BASE_URL, params=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Failed: {method} — {e}")
        return {}

def save_json(name, data):
    (json_dir / f"{name}.json").write_text(json.dumps(data, indent=2))

def save_csv(name, df):
    df.to_csv(processed_dir / f"{name}.csv", index=False)

def safe_filename(name):
    return re.sub(r"[\\/:*?\"<>|]", "", name).replace(" ", "_")

def clean_player_name(name):
    name = re.sub(r"[\[\(].*?[\)\]]", "", str(name))
    name = name.replace("_", " ").replace(".", "").strip()
    return re.sub(r"\s+", " ", name)

def normalize_name(name):
    name = clean_player_name(name)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-z0-9\s.]", "", name.lower())
    return re.sub(r"\s+", " ", name.strip())

# === STEP 1: Fetch combined ATP + WTA standings
def fetch_standings():
    all_rows = []
    for tour in ["ATP", "WTA"]:
        data = fetch_data("get_standings", {"event_type": tour}).get("result", [])
        rows = [{
            "player_key": x.get("player_key"),
            "player": x.get("player"),
            "place": x.get("place"),
            "points": x.get("points"),
            "country": x.get("country"),
            "movement": x.get("movement"),
            "league": x.get("league")
        } for x in data]
        all_rows.extend(rows)
        print(f"✅ Retrieved {len(rows)} {tour} players")

    df_all = pd.DataFrame(all_rows)
    df_all.to_csv(standings_path, index=False)
    print(f"✅ Saved merged standings.csv with {len(df_all)} players")

# === STEP 2: Fetch players using get_players + match parsing
def fetch_players():
    if not upcoming_path.exists():
        print("⚠️ No matches_upcoming.csv found — skipping.")
        return

    df = pd.read_csv(upcoming_path)
    raw_names = set(df["player_A"]).union(df["player_B"])

    individual_names = set()
    for name in raw_names:
        name = re.sub(r"\([^)]*\)", "", str(name))
        parts = re.split(r"/|,|&", name)
        individual_names.update(p.strip() for p in parts if p.strip())

    standings_df = pd.read_csv(standings_path)
    standings_df["player_clean"] = standings_df["player"].apply(normalize_name)
    name_to_key = dict(zip(standings_df["player_clean"], standings_df["player_key"]))

    results = []
    for original in individual_names:
        cleaned = normalize_name(original)
        match = [name for name in name_to_key if partial_token_set_ratio(cleaned, name) >= 85]
        key = name_to_key.get(match[0]) if match else None
        if not key:
            continue

        cache_file = player_dir / f"{key}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                player_data = json.load(f)
        else:
            player_data = fetch_data("get_players", {"player_key": key})
            cache_file.write_text(json.dumps(player_data, indent=2))

        if not player_data.get("result"):
            continue

        info = player_data["result"][0]
        stats = info.get("stats", [])
        best = max(stats, key=lambda s: s.get("season", "0")) if stats else {}

        results.append({
            "player_key": key,
            "player_name": info.get("player_name"),
            "player_country": info.get("player_country"),
            "season": best.get("season"),
            "rank": best.get("rank") or info.get("player_rank"),
            "matches_won": best.get("matches_won"),
            "matches_lost": best.get("matches_lost"),
            "titles": best.get("titles"),
            "type": best.get("type"),
            "points": best.get("points") or info.get("player_points") or 0
        })

    df_out = pd.DataFrame(results)
    df_out.to_csv(players_path, index=False)
    print(f"✅ Saved players.csv with {len(df_out)} rows")
    return len(df), len(individual_names), len(df_out)



# === STEP 3: Fetch H2H remains unchanged
def fetch_h2h():
    if not upcoming_path.exists():
        print("⚠️ No matches_upcoming.csv found — skipping H2H.")
        return

    df = pd.read_csv(upcoming_path)
    summary = []

    pairs = {}
    for _, row in df.iterrows():
        A, B = row["player_A"], row["player_B"]
        key = "__".join(sorted([safe_filename(A), safe_filename(B)]))
        pairs[key] = {
            "player_A": A,
            "player_B": B,
            "match_id": row["match_id"]
        }

    print(f"🔁 Processing {len(pairs)} unique H2H pairs...\n")

    for key, pair in pairs.items():
        A, B, match_id = pair["player_A"], pair["player_B"], pair["match_id"]
        cache_file = h2h_dir / f"{key}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                h2h_data = json.load(f)
            print(f"📦 Cached: {key}")
        else:
            print(f"🌐 Fetching H2H: {A} vs {B}")
            h2h_data = fetch_data("get_H2H", {"first_player_key": A, "second_player_key": B})
            cache_file.write_text(json.dumps(h2h_data, indent=2))

        results = h2h_data.get("result", {}).get("H2H", [])
        A_wins = sum(1 for r in results if r.get("event_winner") == "First Player")
        B_wins = sum(1 for r in results if r.get("event_winner") == "Second Player")
        total = len(results)
        winrate_diff = round((A_wins - B_wins) / total, 4) if total else 0

        summary.append({
            "match_id": match_id,
            "player_A": A,
            "player_B": B,
            "A_wins": A_wins,
            "B_wins": B_wins,
            "total_matches": total,
            "h2h_winrate_diff": winrate_diff
        })

    save_csv("h2h_summary", pd.DataFrame(summary))
    print(f"\n✅ Saved h2h_summary.csv with {len(summary)} rows")
    return len(df), len(summary)
    

# === MAIN ===
if __name__ == "__main__":
    fetch_standings()
    total_matches, total_players_extracted, players_matched = fetch_players()
    h2h_attempted, h2h_matched = fetch_h2h()

    print("\n📊 API Enrichment Summary:")
    print(f"📄 Total matches in matches_upcoming.csv: {total_matches}")
    print(f"👥 Unique player names extracted: {total_players_extracted}")
    print(f"🧬 Players matched + enriched: {players_matched}")
    print()
    print(f"🔁 H2H lookups attempted: {h2h_attempted}")
    print(f"✅ H2H matches with data: {h2h_matched}")
    print(f"❌ H2H with no history: {h2h_attempted - h2h_matched}")
