# CapBot 🎾🤖

**CapBot** is an AI-powered tennis prediction engine designed to identify high-confidence betting opportunities, simulate performance in a virtual sandbox, and provide smart picks daily — without hype or emotion.

---

## 📁 Project Structure

| Folder         | Purpose                                                                 |
|----------------|-------------------------------------------------------------------------|
| `capbot-sim/`  | Virtual betting logic, bankroll updates, stats logging                 |
| `data/`        | Match CSVs and data import scripts                                      
| `model/`       | Finalized ML prediction logic (`predictor.py`, etc.)                   |
| `notebooks/`   | Prototyping models, testing features, scoring daily picks              |
| `backend/`     | Optional API layer to serve model predictions                          |
| `frontend/`    | Flutter (for mobile app) or Streamlit (for MVP web dashboard)          |

---

## 🚧 MVP Goals (Phase 1)
- [ ] Pull ATP/WTA match data via public APIs or CSVs
- [ ] Build a basic ML prediction model (v0.1)
- [ ] Simulate daily bets using a sandbox bankroll
- [ ] Display top 5–10 picks each day based on win probability

---

## 🔮 Future Phases
- Odds integration
- Automatic model tuning
- Daily auto-report generation
- Historical performance dashboard
- Mobile app

---

This is a personal AI project for progressive, low-risk betting experimentation — built like a dev, tested like a scientist.
