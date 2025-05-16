#Updates titles, matches won, losses from players.csv in upcoming_match
#handles only 2 player per cell (GOOD FOR TEAMS)

from pathlib import Path
import pandas as pd
import re, unicodedata
from rapidfuzz.fuzz import partial_token_set_ratio

# === PATHS ===
base_dir = Path("data/api-tennis")
processed_dir = base_dir / "processed"
upcoming_path = Path("data/current/matches_upcoming.csv")
players_path = processed_dir / "players.csv"

# === HELPERS ===
def normalize_name(name):
    name = re.sub(r"\([^)]*\)", "", str(name))
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-z0-9\s.]", "", name.lower())
    return re.sub(r"\s+", " ", name.strip())

# === Inject wins/losses/titles to matches_upcoming.csv ===
def inject_player_stats():
    if not upcoming_path.exists() or not players_path.exists():
        print("❌ Missing input file")
        return

    df = pd.read_csv(upcoming_path)
    players_df = pd.read_csv(players_path)
    players_df["normalized_name"] = players_df["player_name"].apply(normalize_name)

    stats = ["matches_won", "matches_lost", "titles"]
    suffixes = ["A1", "A2", "B1", "B2"]
    for stat in stats:
        for suffix in suffixes:
            col = f"{stat}_{suffix}"
            if col not in df.columns:
                df[col] = 0

    for idx, row in df.iterrows():
        def match_player(name):
            name = normalize_name(name)
            temp = players_df.copy()
            temp["score"] = temp["normalized_name"].apply(lambda x: partial_token_set_ratio(name, x))
            top = temp.loc[temp["score"].idxmax()] if not temp.empty else None
            return top if top is not None and top["score"] >= 85 else None

        A_parts = str(row["player_A"]).split("/")
        B_parts = str(row["player_B"]).split("/")

        matched_players = {
            "A1": match_player(A_parts[0]) if len(A_parts) > 0 else None,
            "A2": match_player(A_parts[1]) if len(A_parts) > 1 else None,
            "B1": match_player(B_parts[0]) if len(B_parts) > 0 else None,
            "B2": match_player(B_parts[1]) if len(B_parts) > 1 else None,
        }

        for label, player in matched_players.items():
            if player is not None:
                for stat in stats:
                    df.at[idx, f"{stat}_{label}"] = pd.to_numeric(player[stat], errors="coerce")

    df.to_csv(upcoming_path, index=False)
    print("✅ Injected detailed doubles stats into matches_upcoming.csv")

    # === Final Summary ===
    total = len(df)
    matches_updated = sum((row[f"matches_won_A1"] > 0 or row[f"matches_won_B1"] > 0) for _, row in df.iterrows())
    no_match_found = sum(all(pd.isna(row[f"matches_won_{sfx}"]) for sfx in suffixes) for _, row in df.iterrows())
    partial_matches = total - matches_updated - no_match_found

    print("\n📊 Players Injection Summary:")
    print(f"🟡 Total upcoming matches: {total}")
    print(f"🟢 Matches updated with stats: {matches_updated}")
    print(f"🔴 Matches skipped: {no_match_found}")
    print(f"   └─ ❌ No fuzzy match found: {no_match_found}")
    print(f"   └─ ⚠️  Match found but incomplete stats: {partial_matches}")

inject_player_stats()
