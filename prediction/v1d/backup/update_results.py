import pandas as pd
import re
from pathlib import Path

# === File Paths ===
source_path = Path("/Users/boroni_4/Documents/CapBot/capbot/prediction/v1d/CapBot_v1d_Predictions_20250517.xlsx")
result_path = Path("/Users/boroni_4/Documents/CapBot/capbot/prediction/v1d/CapBot_v1d_Predictions_20250517_result.xlsx")
match_finished_path = Path("/Users/boroni_4/Documents/CapBot/capbot/data/current/matches_finished.csv")

# === Load Data ===
print("📥 Loading prediction and match result files...")
df = pd.read_excel(source_path, sheet_name="Full Predictions")
mf = pd.read_csv(match_finished_path)
print(f"✅ Loaded {len(df)} predictions and {len(mf)} match results.")

# === Normalize helper ===
def clean_name(name):
    name = re.sub(r"\s*\[\d+\]", "", str(name))
    return name.strip().lower()

print("🧼 Cleaning player names...")
df["player_A_clean"] = df["player_A"].apply(clean_name)
df["player_B_clean"] = df["player_B"].apply(clean_name)
mf["player_A_clean"] = mf["player_A"].apply(clean_name)
mf["player_B_clean"] = mf["player_B"].apply(clean_name)

# === Filter valid results ===
print("🔎 Filtering finished matches with valid winner_code (A/B)...")
mf = mf[mf["winner_code"].isin(["A", "B"])]
print(f"✅ {len(mf)} valid finished matches remaining.")

mf["winner_clean"] = mf.apply(
    lambda row: row["player_A_clean"] if row["winner_code"] == "A" else row["player_B_clean"], axis=1
)

# === Match and Update ===
def resolve_correct_pick(row):
    a, b = row["player_A_clean"], row["player_B_clean"]
    matches = mf[((mf["player_A_clean"] == a) & (mf["player_B_clean"] == b)) |
                 ((mf["player_A_clean"] == b) & (mf["player_B_clean"] == a))]
    if not matches.empty:
        winner_clean = matches.iloc[0]["winner_clean"]
        return row["player_A"] if winner_clean == a else row["player_B"]
    return None

print("🔁 Resolving correct picks...")
df["correct_pick"] = df.apply(resolve_correct_pick, axis=1)
resolved = df["correct_pick"].notnull().sum()
print(f"✅ Resolved {resolved} correct picks.")

print("📊 Assigning status based on prediction result...")
df["status"] = df.apply(
    lambda r: "🟢 CAPPED" if r["capbot_pick"] == r["correct_pick"]
    else ("🔴 FLOP" if pd.notnull(r["correct_pick"]) else "⏳ Awaiting Result"), axis=1
)

print("💾 Saving updated predictions to result Excel file...")
with pd.ExcelWriter(result_path, engine="xlsxwriter") as writer:
    df.drop(columns=["player_A_clean", "player_B_clean"], errors="ignore").to_excel(
        writer, sheet_name="Full Predictions", index=False
    )

print("✅ Done! Updated file saved to:", result_path)