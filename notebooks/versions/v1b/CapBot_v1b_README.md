# 📄 CapBot V1B – Confidence Calibration Report

**Date:** 20250516  
**Report File:** `CapBot_v1b_Confidence_Report_20250516.csv`
**Excel Report:** `CapBot_v1b_Confidence_Report_20250516.xlsx`

---

## 🎯 Objective
To evaluate the baseline model's confidence calibration by analyzing accuracy at various prediction probability thresholds using the **entire historical dataset** (~50279 matches).

---

## 🧠 Methodology
- Trained a logistic regression model using all historical matches
- Predicted win probabilities (`pred_proba`) for each match
- Measured how accurate the model is when its confidence exceeds specific thresholds

---

## 📊 Confidence Threshold Summary
Out of **50279 total matches**:
- **24981 matches** had `pred_proba ≥ 0.5` → Accuracy: **68.02%**
- **15260 matches** had `pred_proba ≥ 0.6` → Accuracy: **75.79%**
- **8345 matches** had `pred_proba ≥ 0.7` → Accuracy: **82.66%**
- **4140 matches** had `pred_proba ≥ 0.8` → Accuracy: **88.36%**
- **1930 matches** had `pred_proba ≥ 0.9` → Accuracy: **92.85%**

---

## 📈 Raw Table View
| Threshold   |   Total Predictions |   Correct Predictions |   Accuracy |
|:------------|--------------------:|----------------------:|-----------:|
| >= 0.6      |               15260 |                 11565 |     0.7579 |
| >= 0.7      |                8345 |                  6898 |     0.8266 |
| >= 0.8      |                4140 |                  3658 |     0.8836 |
| >= 0.9      |                1930 |                  1792 |     0.9285 |

---

## ✅ Insights
- Confidence thresholds correlate positively with accuracy
- Higher confidence yields fewer predictions, but better reliability
- This lays the groundwork for smarter filtering and EV-based strategies

---
