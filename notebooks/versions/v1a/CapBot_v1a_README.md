# 📄 CapBot V1A – Filter Comparison Report

**Date:** 20250516  
**Excel Report:** `CapBot_v1a_Report_20250516.xlsx`

---

## 🎯 Filters Evaluated
| Label | pred_proba ≥ | odds_A ≥ | Description |
|-------|--------------|----------|-------------|
| conf_60_odds_150 | 0.60 | 1.50 | ✅ Realistic baseline filter |
| conf_65_odds_140 | 0.65 | 1.40 | ⚖️ Balanced confidence & odds |
| conf_70_odds_135 | 0.70 | 1.35 | 🎯 Slightly aggressive confidence |
| conf_75_odds_130 | 0.75 | 1.30 | 🔒 Very confident, low risk |

---

# 🧠 Model & Evaluation Details
- **Model Type:** Logistic Regression (`sklearn`)
- **Training Data:** 80% of dataset (randomized)
- **Predictions Evaluated On:** Entire dataset (100%)
- **Runs:** Single unified prediction run (no simulation loop)

---

## 📊 Summary for `conf_60_odds_150`
| Run    |   Accuracy |   Total Bets |   Profit ($) |   ROI (%) |   Bet Accuracy |
|:-------|-----------:|-------------:|-------------:|----------:|---------------:|
| Single |     0.6776 |         1009 |     -8910.65 |     -4.42 |         0.6254 |
---

## 📊 Summary for `conf_65_odds_140`
| Run    |   Accuracy |   Total Bets |   Profit ($) |   ROI (%) |   Bet Accuracy |
|:-------|-----------:|-------------:|-------------:|----------:|---------------:|
| Single |     0.6776 |          529 |     -3328.66 |     -3.15 |         0.6786 |
---

## 📊 Summary for `conf_70_odds_135`
| Run    |   Accuracy |   Total Bets |   Profit ($) |   ROI (%) |   Bet Accuracy |
|:-------|-----------:|-------------:|-------------:|----------:|---------------:|
| Single |     0.6776 |           82 |       579.34 |      3.53 |         0.7195 |
---

## 📊 Summary for `conf_75_odds_130`
| Run    |   Accuracy |   Total Bets |   Profit ($) |   ROI (%) |   Bet Accuracy |
|:-------|-----------:|-------------:|-------------:|----------:|---------------:|
| Single |     0.6776 |           47 |      1165.34 |      12.4 |         0.8085 |
---
