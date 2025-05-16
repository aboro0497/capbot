#!/bin/bash
cd "$(dirname "$0")/.."

echo "🧹 Step 1: Purge old matches"
python data/current/purge_daily.py

echo "🎾 Step 2: Fetch fresh match shell"
python data/current/fetch_daily.py

echo "💰 Step 3: Inject updated odds"
python data/odds/fetch_odds_master.py

echo "📊 Step 4: Enrich with API Tennis data (players + H2H)"
python data/api-tennis/fetch_api_data.py

echo "📈 Step 5: Inject rank + points from standings"
python data/api-tennis/api_standings_data1_to_match.py

echo "🧠 Step 6: Inject player stats (wins/losses/titles)"
python data/api-tennis/api_players_data2_to_match.py

echo "🧠 Step 7: Enrichment Audit for Match_upcoming"
python data/audit/audit_enrichment_accuracy.py

echo "✅ All done at $(date)"
