import pandas as pd
import json
from pathlib import Path

# Load the combined JSON
combined_json_path = Path("data/odds/api_tennis_combined.json")
output_csv_path = Path("data/odds/fixture_odds_flat.csv")

with open(combined_json_path) as f:
    data = json.load(f)

fixtures = data.get("fixtures", [])
odds_by_event = data.get("odds", {})

# Helpers
def safe_float(val):
    try:
        return float(str(val).replace(",", ".").strip())
    except:
        return None

def best_odds_with_betano_first(odds_dict):
    if "Betano" in odds_dict:
        return safe_float(odds_dict["Betano"])
    return max(
        [safe_float(v) for v in odds_dict.values() if safe_float(v) is not None],
        default=None
    )

# Build rows
rows = []
with_odds = 0
for fixture in fixtures:
    event_key = str(fixture.get("event_key", ""))
    event_date = fixture.get("event_date", "")
    event_time = fixture.get("event_time", "")
    player_A = fixture.get("event_first_player", "")
    player_B = fixture.get("event_second_player", "")

    odds_data = odds_by_event.get(event_key, {}).get("Home/Away", {})
    home_odds = odds_data.get("Home", {})
    away_odds = odds_data.get("Away", {})

    odds_A = best_odds_with_betano_first(home_odds)
    odds_B = best_odds_with_betano_first(away_odds)

    if odds_A and odds_B:
        with_odds += 1

    rows.append({
        "event_key": event_key,
        "date": event_date,
        "time": event_time,
        "player_A": player_A,
        "player_B": player_B,
        "odds_A": odds_A,
        "odds_B": odds_B
    })

# Save to CSV
df = pd.DataFrame(rows)
df.to_csv(output_csv_path, index=False)

# Summary
total = len(df)
print(f"\n✅ Saved: {output_csv_path}")
print("📊 Fixture + Odds Summary:")
print(f"🟡 Total fixtures processed: {total}")
print(f"🟢 Fixtures with odds: {with_odds}")
print(f"⚪ Fixtures without odds: {total - with_odds}")
