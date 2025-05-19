import pandas as pd
from pathlib import Path

# === Setup Paths ===
base_dir = Path(__file__).resolve().parent
backup_dir = base_dir / "backup"
today = pd.Timestamp.today().strftime("%Y%m%d")

# === Files ===
pred_file = base_dir / f"CapBot_v1d_Predictions_{today}.xlsx"
old_file = backup_dir / "CapBot_v1d_Predictions_20250517.xlsx"

print(f"📂 Merging into: {pred_file.name}")
print(f"📂 Comparing against old file: {old_file.name}")

# === Load Full Predictions
new_df = pd.read_excel(pred_file, sheet_name="Full Predictions")
old_df = pd.read_excel(old_file, sheet_name="Full Predictions")
new_df["match_id"] = new_df["match_id"].astype(str).str.strip()
old_df["match_id"] = old_df["match_id"].astype(str).str.strip()

combined = pd.concat([new_df, old_df], ignore_index=True).drop_duplicates(subset=["match_id"])
if "date" in combined.columns and "time" in combined.columns:
    combined = combined.sort_values(by=["date", "time"])
print(f"✅ Full Predictions merged: {len(combined)} rows")

# === Load & Merge Filtered Picks
new_filtered = pd.read_excel(pred_file, sheet_name="Filtered Picks")
old_filtered = pd.read_excel(old_file, sheet_name="Filtered Picks")
new_filtered["match_id"] = new_filtered["match_id"].astype(str).str.strip()
old_filtered["match_id"] = old_filtered["match_id"].astype(str).str.strip()

filtered_combined = pd.concat([new_filtered, old_filtered], ignore_index=True)
filtered_combined = filtered_combined.drop_duplicates(subset=["match_id"])
if "date" in filtered_combined.columns and "time" in filtered_combined.columns:
    filtered_combined = filtered_combined.sort_values(by=["date", "time"])
print(f"✅ Filtered Picks merged: {len(filtered_combined)} rows")

# === Load & Merge Summary
new_summary = pd.read_excel(pred_file, sheet_name="Summary")
old_summary = pd.read_excel(old_file, sheet_name="Summary")

summary_combined = pd.concat([new_summary, old_summary], ignore_index=True)
summary_combined = summary_combined.drop_duplicates()
print(f"✅ Summary merged: {len(summary_combined)} rows")

# === Save Back — overwrite all sheets
with pd.ExcelWriter(pred_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    combined.to_excel(writer, sheet_name="Full Predictions", index=False)
    filtered_combined.to_excel(writer, sheet_name="Filtered Picks", index=False)
    summary_combined.to_excel(writer, sheet_name="Summary", index=False)

print(f"✅ All sheets updated in-place: {pred_file.name}")
