import pandas as pd
import numpy as np

# === Load ATP & WTA Files ===
atp_path = "data/historical/processed/matches_2015_2025_atp.csv"
wta_path = "data/historical/processed/matches_2015_2025_wta.csv"

atp_df = pd.read_csv(atp_path)
wta_df = pd.read_csv(wta_path)

# ✅ Optional: Add source column
atp_df["tour"] = "ATP"
wta_df["tour"] = "WTA"

# === Combine into one DataFrame ===
df = pd.concat([atp_df, wta_df], ignore_index=True)
print(f"🧬 Combined rows: {len(df)}")

# === Ensure required columns exist ===
required_cols = ['player_A', 'player_B', 'rank_A', 'rank_B', 'pts_A', 'pts_B', 'odds_A', 'odds_B']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"❌ Missing column: {col}")

# === Handle 'winner' field if not present ===
if "winner" not in df.columns:
    if "winner_code" in df.columns:
        print("🔁 Reconstructing 'winner' column from winner_code (A/B)...")
        df["winner"] = np.where(df["winner_code"] == "A", df["player_A"], df["player_B"])
    else:
        raise ValueError("❌ Neither 'winner' nor 'winner_code' found. Cannot infer winner.")

# === Randomly swap A and B for 50% of rows ===
swap_mask = np.random.rand(len(df)) > 0.5

# Swap player names
df.loc[swap_mask, ['player_A', 'player_B']] = df.loc[swap_mask, ['player_B', 'player_A']].values
# Swap ranks
df.loc[swap_mask, ['rank_A', 'rank_B']] = df.loc[swap_mask, ['rank_B', 'rank_A']].values
# Swap points
df.loc[swap_mask, ['pts_A', 'pts_B']] = df.loc[swap_mask, ['pts_B', 'pts_A']].values
# Swap odds
df.loc[swap_mask, ['odds_A', 'odds_B']] = df.loc[swap_mask, ['odds_B', 'odds_A']].values

# === Generate binary winner_code ===
df["winner_code"] = (df["player_A"] == df["winner"]).astype(int)

# ✅ Verify label distribution
print("🎯 winner_code distribution:\n", df["winner_code"].value_counts())

# === Save final output ===
out_path = "data/historical/processed/matches_2015_2025_combined_balanced.csv"
df.to_csv(out_path, index=False)
print(f"✅ Saved combined & balanced file → {out_path}")

import pandas as pd

# Load the balanced dataset
df = pd.read_csv("data/historical/processed/matches_2015_2025_combined_balanced.csv")

# Sample a few rows
sample = df.sample(10, random_state=42)

# Check winner_code logic
sample["is_label_correct"] = sample.apply(
    lambda row: (row["winner_code"] == 1 and row["player_A"] == row["winner"]) or
                (row["winner_code"] == 0 and row["player_B"] == row["winner"]),
    axis=1
)

print("🧪 Sample verification results:")
print(sample[["player_A", "player_B", "winner", "winner_code", "is_label_correct"]])

# Confirm overall correctness
incorrect = df[
    ~(((df["winner_code"] == 1) & (df["player_A"] == df["winner"])) |
      ((df["winner_code"] == 0) & (df["player_B"] == df["winner"])))
]

if incorrect.empty:
    print("✅ All winner_code values match actual winner after A/B swap.")
else:
    print(f"❌ Mismatch found in {len(incorrect)} rows. Check logic.")
    print(incorrect[["player_A", "player_B", "winner", "winner_code"]].head())

