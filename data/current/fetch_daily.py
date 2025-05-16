# You asked for the fully corrected script.
# Below is your full, clean, and updated CapBot ingestion script — all fixes applied.
import os
import re
import hashlib
import pandas as pd
from datetime import datetime, timedelta
from shutil import copyfile
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIG ---
OUT_DIR = "data/current"
TRACKER_FILE = os.path.join(OUT_DIR, "match_tracker.csv")
os.makedirs(OUT_DIR, exist_ok=True)

# --- HELPERS ---
TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}$")

def looks_like_player(name):
    return bool(name and any(char.isalpha() for char in name) and len(name.split()) <= 4)

def extract_odds(cell):
    try:
        odds_div = cell.find("div", style=lambda s: s and "float:right" in s)
        return odds_div.get_text(strip=True) if odds_div else ""
    except:
        return ""

def safe_generate_match_id(time, player_A, player_B):
    if not time or not player_A or not player_B:
        print(f"⚠️ Skipped match ID — Missing fields: time='{time}', A='{player_A}', B='{player_B}'")
        return None
    key = f"{time}_{player_A}_{player_B}".lower().replace(" ", "_")
    return hashlib.md5(key.encode()).hexdigest()[:10]

def backup_tracker():
    if not os.path.exists(TRACKER_FILE):
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_filename = f"match_tracker.backup_{timestamp}.csv"
    current_backup_path = os.path.join(OUT_DIR, backup_filename)
    copyfile(TRACKER_FILE, current_backup_path)
    print(f"📦 Backup created: {current_backup_path}")

    archive_dir = os.path.join("data", "backup")
    os.makedirs(archive_dir, exist_ok=True)
    all_backups = sorted([f for f in os.listdir(OUT_DIR) if f.startswith("match_tracker.backup_")])
    for old in all_backups[:-1]:
        os.replace(os.path.join(OUT_DIR, old), os.path.join(archive_dir, old))
        print(f"📁 Moved old backup to archive: {old}")
    archived = sorted([f for f in os.listdir(archive_dir) if f.startswith("match_tracker.backup_")])
    for old in archived[:-3]:
        os.remove(os.path.join(archive_dir, old))
        print(f"🗑️ Deleted old archive: {old}")

# --- FETCH ---
def fetch_matches():
    print("\n🔍 Launching stealth Chrome...")
    options = uc.ChromeOptions()
    options.headless = True
    driver = uc.Chrome(options=options)
    print("🌐 Navigating to base page...")
    driver.get("http://livescore.tennis-data.co.uk/")
    WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "livexscores_iframe")))
    print("✅ Switched into iframe.")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div[@id='allzapasy']//tr")))
    print("✅ Match table loaded.")
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("div#allzapasy tr")
    driver.quit()
    return rows

# --- PARSE ---
def parse_matches(rows):
    competition, court, surface = "", "", "Hard"
    matches = []
    i = 0
    now_local = datetime.now()

    while i < len(rows) - 1:
        row = rows[i]
        row_text = row.get_text(separator=" ", strip=True).replace('\\xa0', ' ')
        row_class = row.get("class", [])

        if row_class == [] and any(surf in row_text for surf in [" - Clay", " - Hard", " - Grass"]):
            parts = row_text.rsplit(" - ", 1)
            competition = parts[0].strip()
            surface = parts[1].strip().capitalize()
            i += 1
            continue
        if "hlavicka2" in row_class:
            court = row.get_text(strip=True).replace("\\u00bb", "").strip()
            i += 1
            continue

        row1, row2 = rows[i], rows[i + 1]
        tds1, tds2 = row1.find_all("td"), row2.find_all("td")
        if len(tds1) < 3 or len(tds2) < 3:
            i += 1
            continue

        time_raw = tds1[0].get_text(strip=True)
        if not TIME_PATTERN.match(time_raw):
            i += 1
            continue

        player_A = tds1[2].get_text(strip=True)
        player_B = tds2[1].get_text(strip=True)
        if not looks_like_player(player_A) or not looks_like_player(player_B):
            i += 1
            continue

        match_id = safe_generate_match_id(time_raw, player_A, player_B)
        if not match_id:
            i += 2
            continue

        score_cols_A = [td.get_text(strip=True) for td in tds1[3:7]]
        score_cols_B = [td.get_text(strip=True) for td in tds2[2:6]]

        score_1 = f"{score_cols_A[0]}-{score_cols_B[0]}" if len(score_cols_A) > 0 else ""
        score_2 = f"{score_cols_A[1]}-{score_cols_B[1]}" if len(score_cols_A) > 1 else ""
        score_3 = f"{score_cols_A[2]}-{score_cols_B[2]}" if len(score_cols_A) > 2 else ""

        odds_A = extract_odds(tds1[2])
        odds_B = extract_odds(tds2[1])

        winner = None
        if tds1[2].find("span", class_="winner"):
            winner = "A"
        elif tds2[1].find("span", class_="winner"):
            winner = "B"

        is_inplay = tds1[1].find("img") and "tennisball" in str(tds1[1].find("img").get("src", ""))
        status = "inplay" if is_inplay else "finished" if any(s.strip().isdigit() for s in score_cols_A + score_cols_B) else "upcoming"

        match_time_obj = datetime.strptime(time_raw, "%H:%M").time()
        match_date = (now_local + timedelta(days=1)).strftime("%Y-%m-%d") if status == "upcoming" and match_time_obj < now_local.time() else now_local.strftime("%Y-%m-%d")

        match = {
            "match_id": match_id,
            "date": match_date,
            "time": time_raw,
            "player_A": player_A,
            "player_B": player_B,
            "rank_A": "",
            "rank_B": "",
            "pts_A": "",
            "pts_B": "",
            "odds_A": odds_A,
            "odds_B": odds_B,
            "surface": surface,
            "series": competition,
            "court": court,
            "round": "",
            "season": now_local.year,
            "score_1": score_1,
            "score_2": score_2,
            "score_3": score_3,
            "winner_code": winner,
            "status": status,
            "last_updated": now_local.strftime("%Y-%m-%d %H:%M"),
            "competition": competition,
            "winner": winner
        }

        matches.append(match)
        i += 2

    return matches

# --- UPDATE TRACKER ---
def update_tracker(matches):
    unified_columns = [
        "match_id", "time", "player_A", "player_B",
        "score_1", "score_2", "score_3", "competition", "court", "winner",
        "odds_A", "odds_B", "last_updated", "status", "date",
        "rank_A", "rank_B", "pts_A", "pts_B", "surface",
        "series", "round", "season", "winner_code"
    ]

    new_df = pd.DataFrame(matches)
    for col in unified_columns:
        if col not in new_df.columns:
            new_df[col] = ""

    if new_df["match_id"].isnull().any():
        print("❌ ERROR: Some match_id values are missing. Aborting update.")
        print(new_df[new_df["match_id"].isnull()][["time", "player_A", "player_B"]])
        return

    new_df = new_df[unified_columns]
    new_df.set_index("match_id", inplace=True)

    if os.path.exists(TRACKER_FILE):
        backup_tracker()
        existing = pd.read_csv(TRACKER_FILE)
        existing = existing.astype(str).set_index("match_id")
        new_df = new_df.astype(str)

        existing.update(new_df)
        combined = pd.concat([existing, new_df[~new_df.index.isin(existing.index)]])
        combined.reset_index(inplace=True)

        combined_ids = set(combined.set_index("match_id").index)
        existing_ids = set(existing.index)
        removed_ids = existing_ids - combined_ids
        removed = len(removed_ids)

        added = len(combined_ids - existing_ids)
        updated = sum(
            not existing.loc[mid].equals(new_df.loc[mid])
            for mid in combined_ids & existing_ids if mid in new_df.index
        )
    else:
        combined = new_df.reset_index()
        added, updated, removed, removed_ids = len(combined), 0, 0, set()

    combined.to_csv(TRACKER_FILE, index=False)
    combined.to_excel(os.path.join(OUT_DIR, "match_tracker.xlsx"), index=False) 
    combined[combined.status == "upcoming"].to_csv(os.path.join(OUT_DIR, "matches_upcoming.csv"), index=False)
    combined[combined.status == "inplay"].to_csv(os.path.join(OUT_DIR, "matches_inplay.csv"), index=False)
    combined[combined.status == "finished"].to_csv(os.path.join(OUT_DIR, "matches_finished.csv"), index=False)

    upcoming = (combined.status == "upcoming").sum()
    inplay = (combined.status == "inplay").sum()
    finished = (combined.status == "finished").sum()
    total = len(combined)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n📊 Current Data Audit Summary — {timestamp}")
    print("──────────────────────────────────────────────")
    print("\n🧾 Match Tracker:")
    print(f"🔼 Added Matches: {added}")
    print(f"🔁 Updated Matches: {updated}")
    if removed > 0:
        print(f"🗑️  ❗REMOVED Matches Detected: {removed} → {sorted(list(removed_ids))}")
    else:
        print(f"🗑️  Removed Matches: 0 ✅ (No data loss)")
    print(f"📈 Total Matches in Tracker: {total}")
    print("\n📂 Snapshots:")
    print(f"📌 Upcoming: {upcoming}")
    print(f"🎾 In-Play: {inplay}")
    print(f"✅ Finished: {finished}")
    print("\n✅ Tracker + snapshots updated")

# --- RUN ---
if __name__ == "__main__":
    rows = fetch_matches()
    matches = parse_matches(rows)
    update_tracker(matches)
