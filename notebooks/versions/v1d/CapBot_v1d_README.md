# 📄 CapBot V1D – EV + Kelly Betting Strategy

**Date:** 20250517  
**Excel Report:** `CapBot_v1d_Report_20250517.xlsx`

---

## 🎯 Strategy
- Train logistic regression on 80% of dataset
- Predict on all matches (100%)
- Calculate:
  - **Expected Value** = (pred_proba × odds_A) - 1
  - **Kelly Fraction** = (b × p - q) / b, clipped to [0, 1]
- Stake = Kelly % × $200 base unit
- Only bet where **EV ≥ 5%**

---

## 📊 Performance Summary
- **Model Accuracy:** 0.6776
- **EV Bets:** 2008 matches
- **Total Staked:** $26321.06
- **Profit:** $3514.32
- **ROI:** 13.35%
- **Bet Accuracy:** 0.6907

---

## ✅ Notes
- Bets are dynamically sized based on confidence + odds
- EV ensures edge; Kelly controls risk
- This strategy balances ROI + bankroll growth

---
