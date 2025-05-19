import pandas as pd

# === Load all 3 files ===
upcoming = pd.read_csv("data/current/matches_upcoming.csv")
tracker = pd.read_csv("data/current/match_tracker.csv")
finished = pd.read_csv("data/current/matches_finished.csv")

# === Normalize match_id for safety ===
for df in [upcoming, tracker, finished]:
    df["match_id"] = df["match_id"].astype(str).str.strip()

# === 1. Check for duplicate match_id in tracker ===
dupes = tracker["match_id"].duplicated().sum()
print(f"🔁 Duplicate match_id in tracker: {dupes}")

# === 2. Check overlap of finished matches in tracker ===
in_finished = finished["match_id"].isin(tracker["match_id"])
print(f"✅ Finished match_ids found in tracker: {in_finished.sum()} / {len(finished)}")

# === 3. Compare statuses for finished matches (if 'status' exists) ===
merged = finished.merge(tracker, on="match_id", suffixes=("_finished", "_tracker"))

if "status" in merged.columns:
    wrong_status = merged[
        ~merged["status"].isin(["🟢 CAPPED", "🔴 FLOP", "finished"])
    ]
    print(f"⚠️ Finished matches with non-final tracker status: {len(wrong_status)}")
    if len(wrong_status):
        print(wrong_status[["match_id", "player_A_finished", "player_B_finished", "status", "winner_code"]].head())
else:
    print("⚠️ Tracker file has no 'status' column. Skipping status comparison for finished matches.")

# === 4. Check if matches in upcoming are actually finished in tracker ===
merged2 = upcoming.merge(tracker, on="match_id", suffixes=("_upcoming", "_tracker"))

if "status" in merged2.columns:
    conflict = merged2[merged2["status"].isin(["🟢 CAPPED", "🔴 FLOP", "finished"])]
    print(f"❌ Matches still in 'upcoming' that have been marked finished in tracker: {len(conflict)}")
    if len(conflict):
        print(conflict[["match_id", "player_A_upcoming", "player_B_upcoming", "status"]].head())
else:
    print("⚠️ Merged tracker has no 'status' column — cannot check for upcoming/finished conflicts.")
