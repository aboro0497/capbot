# 📄 CapBot v1 – Release Notes

**Date:** 20250516  
**Summary File:** `summary_v1.csv`  
**Excel Report:** `CapBot_v1_Report_20250516.xlsx`  
**Model Version:** v1  
**Strategy Version:** v1  

---

## 🧠 Model Info
- **Type:** Logistic Regression (`sklearn`)
- **Train/Test Split:** 75/25 stratified (10 different seeds)
- **Features Used:**  `rank_A`, `rank_B`, `pts_A`, `pts_B`, `odds_A`, `odds_B`
- **Target:** `winner_code` → 1 = Player A wins, 0 = Player B wins

---

## 📂 Dataset
- **Source File:** `/Users/boroni_4/Documents/CapBot/capbot/notebooks/versions/v1/../../../data/historical/processed/matches_2015_2025_combined_balanced.csv`
- **Filtered Rows (after cleanup):** 50279

---

## 📊 Last Run Snapshot
- **Accuracy:** 0.6731  
- **Confusion Matrix:**
```
4274	1991
2118	4187
```

---

## 💸 Betting Strategy
- Bet if `pred_proba >= 0.60` and `odds_A >= 1.50`
- Flat bet of $200 per match

---

## 📈 10 Simulation Summary

| Run     |   Accuracy |   Total Bets |   Profit ($) |   ROI (%) |   Bet Accuracy |
|:--------|-----------:|-------------:|-------------:|----------:|---------------:|
| 1       |     0.6799 |          257 |      -776.66 |     -1.51 |         0.6459 |
| 2       |     0.6757 |          268 |     -3839.32 |     -7.16 |         0.6082 |
| 3       |     0.6797 |          236 |     -4062    |     -8.61 |         0.6017 |
| 4       |     0.6799 |          261 |     -3443.32 |     -6.6  |         0.613  |
| 5       |     0.6745 |          235 |     -3021.99 |     -6.43 |         0.6085 |
| 6       |     0.6777 |          203 |     -4200    |    -10.34 |         0.5911 |
| 7       |     0.6753 |          253 |     -1019.32 |     -2.01 |         0.6364 |
| 8       |     0.6795 |          277 |      1224.01 |      2.21 |         0.6643 |
| 9       |     0.6823 |          230 |     -4080    |     -8.87 |         0.6    |
| 10      |     0.6731 |          251 |     -3536    |     -7.04 |         0.6135 |
| Average |     0.6778 |          247 |     -2675.46 |     -5.64 |         0.6183 |

---

## ✅ Notes
- v1 is the benchmark with no external features, EV filters, or parlay logic yet.
- Future versions will include EV logic, SHAP explainability, bankroll optimization.

---
