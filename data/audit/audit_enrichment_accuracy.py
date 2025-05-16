import pandas as pd
from pathlib import Path
import re, unicodedata
from rapidfuzz.fuzz import partial_token_set_ratio

# === Paths ===
upcoming_path = Path("data/current/matches_upcoming.csv")
players_path = Path("data/api-tennis/processed/players.csv")
standings_path = Path("data/api-tennis/processed/standings.csv")
detailed_xlsx_out = Path("data/audit/enrichment_audit_detailed.xlsx")

# === Normalize Function ===
def normalize_name(name):
    name = re.sub(r"\([^)]*\)", "", str(name))
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-z0-9\s.]", "", name.lower())
    return re.sub(r"\s+", " ", name.strip())

# === Load Data ===
upcoming = pd.read_csv(upcoming_path)
players_df = pd.read_csv(players_path)
standings_df = pd.read_csv(standings_path)

players_df["normalized_name"] = players_df["player_name"].apply(normalize_name)
standings_df["normalized_name"] = standings_df["player"].apply(normalize_name)

# === Helper: Best fuzzy match from dataframe ===
def match_player(name, df):
    name = normalize_name(name)
    df = df.copy()
    df["score"] = df["normalized_name"].apply(lambda x: partial_token_set_ratio(name, x))
    top = df.loc[df["score"].idxmax()] if not df.empty else None
    return top if top is not None and top["score"] >= 85 else None

# === Audit Execution ===
audit = []
detailed_rows = []
fully = partially = missing = 0

for _, row in upcoming.iterrows():
    match_id = row["match_id"]
    player_groups = {
        "A1": row["player_A"].split("/")[0].strip() if pd.notna(row["player_A"]) else "",
        "A2": row["player_A"].split("/")[1].strip() if "/" in str(row["player_A"]) else "",
        "B1": row["player_B"].split("/")[0].strip() if pd.notna(row["player_B"]) else "",
        "B2": row["player_B"].split("/")[1].strip() if "/" in str(row["player_B"]) else "",
    }

    filled_stats = 0

    for label, name in player_groups.items():
        if not name:
            continue

        norm = normalize_name(name)

        player_match = match_player(norm, players_df)
        stand_match = match_player(norm, standings_df)

        injected = {
            "won": row.get(f"matches_won_{label}"),
            "lost": row.get(f"matches_lost_{label}"),
            "titles": row.get(f"titles_{label}"),
            "rank": row.get(f"rank_{label}"),
            "points": row.get(f"pts_{label}"),
        }

        actual = {
            "won": player_match["matches_won"] if player_match is not None else None,
            "lost": player_match["matches_lost"] if player_match is not None else None,
            "titles": player_match["titles"] if player_match is not None else None,
            "rank": stand_match["place"] if stand_match is not None else None,
            "points": stand_match["points"] if stand_match is not None else None,
        }

        def safe_match(val1, val2):
            if pd.isna(val1) or pd.isna(val2):
                return None
            return int(val1) == int(val2)

        matches = {
            "won_match": safe_match(injected["won"], actual["won"]),
            "lost_match": safe_match(injected["lost"], actual["lost"]),
            "titles_match": safe_match(injected["titles"], actual["titles"]),
            "rank_match": safe_match(injected["rank"], actual["rank"]),
            "points_match": safe_match(injected["points"], actual["points"]),
        }

        valid_matches = [m for m in matches.values() if m is not None and m is True]
        filled_stats += len(valid_matches)

        detailed_rows.append({
            "match_id": match_id,
            "player_col": label,
            "name": name,
            "fuzzy_score_players": player_match["score"] if player_match is not None else 0,
            "fuzzy_score_standings": stand_match["score"] if stand_match is not None else 0,

            "matches_won_injected": injected["won"],
            "matches_won_actual": actual["won"],
            "matches_won_match": matches["won_match"],

            "matches_lost_injected": injected["lost"],
            "matches_lost_actual": actual["lost"],
            "matches_lost_match": matches["lost_match"],

            "titles_injected": injected["titles"],
            "titles_actual": actual["titles"],
            "titles_match": matches["titles_match"],

            "rank_injected": injected["rank"],
            "rank_actual": actual["rank"],
            "rank_match": matches["rank_match"],

            "points_injected": injected["points"],
            "points_actual": actual["points"],
            "points_match": matches["points_match"],
        })

    if filled_stats >= 4:
        status = "✅ Fully enriched"
        fully += 1
    elif filled_stats > 0:
        status = "⚠️ Partially enriched"
        partially += 1
    else:
        status = "❌ Missing all data"
        missing += 1

    audit.append({"match_id": match_id, "status": status})

# === Summary Stats ===
total = len(upcoming)
accuracy_pct = round((fully / total) * 100, 2) if total > 0 else 0

summary_stats = pd.DataFrame([
    {"Metric": "Total Matches from matches_upcoming.csv", "Value": total},
    {"Metric": "✅ Fully Enriched Matches", "Value": fully},
    {"Metric": "⚠️ Partially Enriched Matches", "Value": partially},
    {"Metric": "❌ Matches with No Enrichment", "Value": missing},
    {"Metric": "📊 Accuracy % (Fully / Total)", "Value": f"{accuracy_pct}%"}
])

# === Save All to XLSX ===
from pandas import ExcelWriter

with ExcelWriter(detailed_xlsx_out) as writer:
    pd.DataFrame(detailed_rows).to_excel(writer, sheet_name="Detailed Audit", index=False)
    pd.DataFrame(audit).to_excel(writer, sheet_name="Match Summary", index=False)
    summary_stats.to_excel(writer, sheet_name="Summary Stats", index=False)

# === Console Output ===
print("\n📊 CapBot Enrichment Accuracy Summary")
print("\u2500" * 45)
print(f"📆 Total Matches (from matches_upcoming.csv) : {total}")
print(f"✅ Fully Enriched Matches     : {fully}")
print(f"⚠️ Partially Enriched Matches : {partially}")
print(f"❌ Missing All Data           : {missing}")
print(f"📊 Accuracy                   : {accuracy_pct}%")
print(f"\n📊 All results saved to: {detailed_xlsx_out}")
