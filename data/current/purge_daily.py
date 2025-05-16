import os
import pandas as pd

# --- CONFIG ---
OUT_DIR = "data/current"
TRACKER_FILE = os.path.join(OUT_DIR, "match_tracker.csv")
UPCOMING_FILE = os.path.join(OUT_DIR, "matches_upcoming.csv")
INPLAY_FILE = os.path.join(OUT_DIR, "matches_inplay.csv")

# --- CLEAN TRACKER ---
df = pd.read_csv(TRACKER_FILE)
original_count = len(df)

# Drop rows where status is 'upcoming' or 'inplay'
df = df[~df['status'].str.lower().isin(['upcoming', 'inplay'])]
removed_count = original_count - len(df)

# Save cleaned tracker
df.to_csv(TRACKER_FILE, index=False)

# --- DELETE SNAPSHOTS ---
deleted = []
for file in [UPCOMING_FILE, INPLAY_FILE]:
    if os.path.exists(file):
        os.remove(file)
        deleted.append(os.path.basename(file))

# --- OUTPUT ---
print(f"✅ Removed {removed_count} matches with status 'upcoming' or 'inplay'.")
print(f"💾 Tracker now has {len(df)} finished matches.")
if deleted:
    print(f"🗑️ Deleted snapshot(s): {', '.join(deleted)}")
else:
    print("📂 No snapshot files found to delete.")
