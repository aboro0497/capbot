# 📄 CapBot V1C – EV Betting Strategy

**Date:** 20250516  
**Excel Report:** `CapBot_v1c_Report_20250516.xlsx`

---

## 🎯 Strategy
- Train logistic regression model on 80% of dataset
- Predict probabilities on all matches (100%)
- Calculate **Expected Value**: `EV = (pred_proba × odds_A) - 1`
- Keep bets with **EV ≥ 5%**

---

## 📊 Performance Summary
- **Model Accuracy:** 0.6776
- **Total Bets (EV ≥ 5%):** 2008
- **Bet Accuracy:** 0.6907
- **Total Profit:** $5905.72
- **ROI:** 1.47%

---

## ✅ Notes
- This version filters strictly based on **positive expected value**
- Odds and probabilities are both required to justify each pick
- Suitable for real-world betting where value beats volume

---
