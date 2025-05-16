# Updates point & rank from standing.csv in matches_upcoming.csv
# Handles singles (1 player per cell) and doubles (2 players per cell)

from pathlib import Path
import pandas as pd
import re, unicodedata
from rapidfuzz.fuzz import partial_token_set_ratio

# === PATHS ===
base_dir = Path("data/api-tennis")
processed_dir = base_dir / "processed"
upcoming_path = Path("data/current/matches_upcoming.csv")
players_path = processed_dir / "standings.csv"

# === HELPERS ===
def normalize_name(name):
    name = re.sub(r"\([^)]*\)", "", str(name))
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-z0-9\s.]", "", name.lower())
    return re.sub(r"\s+", " ", name.strip())

# === MAIN FUNCTION ===
def inject_rank_points_doubles():
    if not upcoming_path.exists() or not players_path.exists():
        print("❌ Missing input file")
        return

    df = pd.read_csv(upcoming_path)
    players_df = pd.read_csv(players_path)
    players_df["normalized_name"] = players_df["player"].apply(normalize_name)

    # Remove legacy columns if present
    for col in ["rank_A", "rank_B", "pts_A", "pts_B"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    # Ensure new columns exist in correct order
    col_order = [
        "rank_A1", "rank_A2", "rank_B1", "rank_B2",
        "pts_A1", "pts_A2", "pts_B1", "pts_B2"
    ]
    for col in col_order:
        if col not in df.columns:
            df.insert(len(df.columns), col, None)

    matched_count = 0
    no_match_found = 0
    partial_matches = 0

    for idx, row in df.iterrows():
        A_parts = str(row["player_A"]).split("/")
        B_parts = str(row["player_B"]).split("/")

        def match_player(name):
            name = normalize_name(name)
            temp = players_df.copy()
            temp["score"] = temp["normalized_name"].apply(lambda x: partial_token_set_ratio(name, x))
            top = temp.loc[temp["score"].idxmax()] if not temp.empty else None
            return top if top is not None and top["score"] >= 85 else None

        A1 = match_player(A_parts[0]) if len(A_parts) > 0 else None
        A2 = match_player(A_parts[1]) if len(A_parts) > 1 else None
        B1 = match_player(B_parts[0]) if len(B_parts) > 0 else None
        B2 = match_player(B_parts[1]) if len(B_parts) > 1 else None

        # Inject if match found
        if A1 is not None:
            df.at[idx, "rank_A1"] = pd.to_numeric(A1["place"], errors="coerce")
            df.at[idx, "pts_A1"] = pd.to_numeric(A1["points"], errors="coerce")
        if A2 is not None:
            df.at[idx, "rank_A2"] = pd.to_numeric(A2["place"], errors="coerce")
            df.at[idx, "pts_A2"] = pd.to_numeric(A2["points"], errors="coerce")
        if B1 is not None:
            df.at[idx, "rank_B1"] = pd.to_numeric(B1["place"], errors="coerce")
            df.at[idx, "pts_B1"] = pd.to_numeric(B1["points"], errors="coerce")
        if B2 is not None:
            df.at[idx, "rank_B2"] = pd.to_numeric(B2["place"], errors="coerce")
            df.at[idx, "pts_B2"] = pd.to_numeric(B2["points"], errors="coerce")

        # Summary tracking
        matches_found = [A1, A2, B1, B2]
        filled = sum(p is not None for p in matches_found)
        if filled == 4:
            matched_count += 1
        elif filled > 0:
            partial_matches += 1
        else:
            no_match_found += 1

    df.to_csv(upcoming_path, index=False)
    print("✅ Injected rank + points for A1/A2 and B1/B2 into matches_upcoming.csv")

    # === Summary ===
    total = len(df)
    print("\n📊 Standings Injection Summary:")
    print(f"🟡 Total upcoming matches: {total}")
    print(f"🟢 Matches updated with stats: {matched_count}")
    print(f"🔴 Matches skipped: {no_match_found}")
    print(f"   └─ ❌ No fuzzy match found: {no_match_found}")
    print(f"   └─ ⚠️  Match found but incomplete stats: {partial_matches}")

# === RUN ===
inject_rank_points_doubles()
