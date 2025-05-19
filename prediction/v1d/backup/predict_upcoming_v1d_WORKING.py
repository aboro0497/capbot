#V1 - Doesnt run if odds are missing

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
import os
import re

# === Config ===
pd.set_option('future.no_silent_downcasting', True)
today = datetime.today().strftime("%Y%m%d")
base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
project_root = base_dir.parents[2]

model_path = project_root / "capbot" / "model" / "CapBot_v1d_model.pkl"
data_path = project_root / "capbot" / "data" / "current" / "matches_upcoming.csv"
match_finished_path = project_root / "capbot" / "data" / "current" / "matches_finished.csv"
xlsx_path = base_dir / f"CapBot_v1d_Predictions_{today}.xlsx"

# === Load match data ===
df = pd.read_csv(data_path)
df["rank_A"] = df[["rank_A1", "rank_A2"]].mean(axis=1)
df["rank_B"] = df[["rank_B1", "rank_B2"]].mean(axis=1)
df["pts_A"] = df[["pts_A1", "pts_A2"]].mean(axis=1)
df["pts_B"] = df[["pts_B1", "pts_B2"]].mean(axis=1)

numeric_cols = ['rank_A', 'rank_B', 'pts_A', 'pts_B', 'odds_A', 'odds_B']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=numeric_cols)

if 'player_A' not in df.columns:
    df["player_A"] = df["player_A1"].fillna("") + "/" + df["player_A2"].fillna("")
if 'player_B' not in df.columns:
    df["player_B"] = df["player_B1"].fillna("") + "/" + df["player_B2"].fillna("")

df["player_A"] = df["player_A"].str.strip("/").replace("/", " / ")
df["player_B"] = df["player_B"].str.strip("/").replace("/", " / ")
df["date"] = df["date"]
df["time"] = df["time"] if "time" in df.columns else ""

# === Model ===
model = joblib.load(model_path)
X = df[numeric_cols]
df["pred_proba"] = model.predict_proba(X)[:, 1]  # P(Player A wins)

# === CapBot Predictions
df["capbot_pick"] = np.where(df["pred_proba"] >= 0.5, df["player_A"], df["player_B"])
df["confidence"] = df["pred_proba"]
df["odds"] = np.where(df["capbot_pick"] == df["player_A"], df["odds_A"], df["odds_B"])
df["ev"] = df["confidence"] * df["odds"] - 1
b = df["odds"] - 1
p = df["confidence"]
q = 1 - p
df["kelly"] = ((b * p - q) / b).clip(lower=0, upper=1)
df["stake"] = df["kelly"] * 200
df["rank_score"] = df["ev"] * 0.5 + df["confidence"] * 0.3 + df["kelly"] * 0.2

# === Merge Excel if exists (update odds only)
if xlsx_path.exists():
    try:
        print("📥 Merging with existing XLSX: only updating odds_A and odds_B")
        existing = pd.read_excel(xlsx_path, sheet_name="Full Predictions")
        existing.set_index("match_id", inplace=True)
        df.set_index("match_id", inplace=True)

        for field in ["odds_A", "odds_B"]:
            df[field] = df[field].astype(str)
            existing[field] = existing[field].astype(str)
            existing.update(df[[field]])

        new_matches = df[~df.index.isin(existing.index)]
        df = pd.concat([existing, new_matches]).reset_index()

    except Exception as e:
        print("⚠️ Failed to load existing prediction file:", e)
        df.reset_index(inplace=True)

# === Resolve correct_pick and status using matches_finished.csv
if match_finished_path.exists():
    print("📥 Loading matches_finished.csv for result resolution...")
    mf = pd.read_csv(match_finished_path)

    def clean_name(name):
        name = re.sub(r"\s*\[\d+\]", "", str(name))
        return name.strip().lower()

    print("🧼 Cleaning player names...")
    df["player_A_clean"] = df["player_A"].apply(clean_name)
    df["player_B_clean"] = df["player_B"].apply(clean_name)
    mf["player_A_clean"] = mf["player_A"].apply(clean_name)
    mf["player_B_clean"] = mf["player_B"].apply(clean_name)

    print("🔎 Filtering finished matches with valid winner_code (A/B)...")
    mf = mf[mf["winner_code"].isin(["A", "B"])]
    print(f"✅ {len(mf)} valid finished matches remaining.")

    mf["winner_clean"] = mf.apply(
        lambda row: row["player_A_clean"] if row["winner_code"] == "A" else row["player_B_clean"], axis=1
    )

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

    df.drop(columns=["player_A_clean", "player_B_clean"], inplace=True, errors="ignore")
else:
    print("❌ matches_finished.csv not found — skipping result resolution")
    df["correct_pick"] = None
    df["status"] = ""

# === Tag Picks (AFTER result resolution)
def tag_pick(row):
    if row["stake"] <= 0 or row["ev"] < 0.05:
        return "💤 Skip Worthy"
    elif row["confidence"] >= 0.85 and row["ev"] < 0.1:
        return "✅ Safe Pick"
    elif row["confidence"] >= 0.60 and row["ev"] >= 0.10:
        return "⚡ Smart Pick"
    elif row["confidence"] < 0.60 and row["ev"] >= 0.20:
        return "🎯 High Value"
    elif row["confidence"] < 0.50 and row["ev"] >= 0.15:
        return "💥 Wild Upset"
    else:
        return "⚡ Smart Pick"

df = df.sort_values(by="rank_score", ascending=False)
df["pick_tag"] = df.apply(tag_pick, axis=1)
picks = df[(df["ev"] >= 0.05) & (df["stake"] > 0)].copy()
picks = picks.sort_values(by="rank_score", ascending=False)
picks["pick_tag"] = picks.apply(tag_pick, axis=1)

# === Summary ===
summary_rows = [
    {
        "Type": "Full", "Date": today, "Total Matches": len(df),
        "Correct": df["capbot_pick"].eq(df["correct_pick"]).sum(),
        "Accuracy": round(df["capbot_pick"].eq(df["correct_pick"]).mean(), 4),
        "Average EV": round(df["ev"].mean(), 4),
        "Average Stake": round(df["stake"].mean(), 2),
        "Average Proba": round(df["confidence"].mean(), 4)
    },
    {
        "Type": "Filtered", "Date": today, "Total Matches": len(picks),
        "Correct": picks["capbot_pick"].eq(picks["correct_pick"]).sum(),
        "Accuracy": round(picks["capbot_pick"].eq(picks["correct_pick"]).mean(), 4),
        "Average EV": round(picks["ev"].mean(), 4),
        "Average Stake": round(picks["stake"].mean(), 2),
        "Average Proba": round(picks["confidence"].mean(), 4)
    }
]
summary_df = pd.DataFrame(summary_rows)

# === Export ===
columns_to_export = [
    "match_id", "date", "time", "player_A", "player_B", "capbot_pick", "pick_tag",
    "odds_A", "odds_B", "confidence", "ev", "kelly", "stake", "rank_score", "correct_pick", "status"
]

with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
    df[columns_to_export].to_excel(writer, sheet_name="Full Predictions", index=False)
    picks[columns_to_export].to_excel(writer, sheet_name="Filtered Picks", index=False)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

    legend = pd.DataFrame({
        "Tag": [
            "✅ Safe Pick", "⚡ Smart Pick", "🎯 High Value", "💥 Wild Upset", "💤 Skip Worthy"
        ],
        "Description": [
            "Very high probability (>85%) but low EV (e.g. short odds)",
            "Medium-high confidence (~60–85%) and solid EV (≥10%)",
            "Lower probability (<60%) but very high EV (≥20%)",
            "Probability <50%, odds usually 3.0+, but still profitable EV (≥15%)",
            "EV < 5% or stake = 0 — unlikely to be selected anyway"
        ]
    })
    legend.to_excel(writer, sheet_name="Filtered Picks", startrow=len(picks) + 3, index=False)

print(f"✅ XLSX report saved to: {xlsx_path.resolve()}")
