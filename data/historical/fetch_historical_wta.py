# data/historical/fetch_historical_wta.py

import os
import pandas as pd
import requests
from bs4 import BeautifulSoup

RAW_DIR = "data/historical/raw"
CSV_OUT = "data/historical/processed/matches_2015_2025_wta.csv"
XLSX_OUT = "data/historical/processed/matches_2015_2025_wta.xlsx"
os.makedirs(RAW_DIR, exist_ok=True)

BASE_URL = "http://www.tennis-data.co.uk/"
INDEX_PAGE = BASE_URL + "alldata.php"

def scrape_and_download():
    print("\n🔍 Scraping .xlsx links from alldata.php...")
    try:
        resp = requests.get(INDEX_PAGE, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.find_all("a", href=True)
    except Exception as e:
        print(f"❌ Failed to scrape index page: {e}")
        return

    xlsx_links = sorted(set(link["href"] for link in links if link["href"].endswith(".xlsx")))

    for link in xlsx_links:
        file_name = link.split("/")[-1]
        if not file_name.replace(".xlsx", "").isdigit():
            continue

        year = int(file_name.replace(".xlsx", ""))
        if not (2015 <= year <= 2025):
            continue

        suffix = "_WTA" if "/w/" in link or f"{year}w" in link else "_ATP"
        clean_file_name = f"{year}{suffix}.xlsx"

        full_url = BASE_URL.rstrip("/") + "/" + link.lstrip("/")
        out_path = os.path.join(RAW_DIR, clean_file_name)

        if os.path.exists(out_path):
            print(f"⚠️ Already exists: {clean_file_name}, skipping.")
            continue

        print(f"⬇️ Downloading {clean_file_name} from {full_url} ...")
        try:
            resp = requests.get(full_url, timeout=15)
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"✅ Saved: {clean_file_name}")
        except Exception as e:
            print(f"❌ Failed to download {clean_file_name}: {e}")

    print("\n✅ All .xlsx files downloaded to raw/ directory.\n")

def load_and_clean_wta():
    all_matches = []

    for file in os.listdir(RAW_DIR):
        if not file.endswith("_WTA.xlsx"):
            continue

        file_path = os.path.join(RAW_DIR, file)
        print(f"\n🔍 Inspecting {file_path}...")

        try:
            df = pd.read_excel(file_path, sheet_name=0)
        except Exception as e:
            print(f"❌ Failed to read {file_path}: {e}")
            continue

        print(f"📊 Columns in {file}: {df.columns.tolist()}")
        df.columns = [c.strip().lower() for c in df.columns]

        if df.columns[0] != "wta":
            print(f"⚠️ Skipping non-WTA file: {file}")
            continue

        required = ["date", "winner", "loser"]
        if not all(col in df.columns for col in required):
            print(f"⚠️ Missing required fields in {file}")
            continue

        rename_map = {
            "date": "date",
            "winner": "player_A",
            "loser": "player_B",
            "wrank": "rank_A",
            "lrank": "rank_B",
            "wpts": "pts_A",
            "lpts": "pts_B",
            "b365w": "odds_A",
            "b365l": "odds_B",
            "surface": "surface",
            "series": "series",
            "court": "court",
            "round": "round"
        }

        selected = [col for col in rename_map if col in df.columns]
        df = df[selected].rename(columns={col: rename_map[col] for col in selected})

        try:
            year = int(file[:4])
        except:
            year = None

        df["season"] = year
        df["player_A"] = df["player_A"].astype(str).str.title()
        df["player_B"] = df["player_B"].astype(str).str.title()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df[df["date"] <= pd.Timestamp.today()]
        df["winner_code"] = "A"

        df.dropna(subset=["player_A", "player_B", "date"], inplace=True)
        df.drop_duplicates(inplace=True)
        all_matches.append(df)

    if all_matches:
        os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
        final_df = pd.concat(all_matches, ignore_index=True)

        # ✅ Save CSV (for ML)
        final_df.to_csv(CSV_OUT, index=False)

        # ✅ Save Excel (for inspection)
        final_df.to_excel(XLSX_OUT, index=False)

        print(f"\n✅ Done. Final WTA matches saved: {len(final_df)} rows.")
        print(f"📁 CSV:  {CSV_OUT}")
        print(f"📁 XLSX: {XLSX_OUT}")
    else:
        print("❌ No WTA data to save.")

if __name__ == "__main__":
    scrape_and_download()
    load_and_clean_wta()
