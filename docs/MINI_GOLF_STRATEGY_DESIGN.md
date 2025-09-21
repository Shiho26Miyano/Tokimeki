# Mini Golf Strategy Tool — Executive MVP Summary

## Core Concept
- **Flagship Feature**: **CaddieAlpha™ – Risk-Reward Analyzer**
- Target Audience: Hedge fund leaders, Goldman Sachs executives
- Value Proposition: Play golf like managing a portfolio — press edges, avoid blow-ups, respect risk budgets.

## How It Works
- Uses GolfCourse API data:
  - Course ratings, slope, bogey ratings
  - Tee sets (male/female, distances)
  - Hole-by-hole details (par, yardage, handicap)
- Derives quant-style metrics:
  - **Volatility** (slope + hole handicap)
  - **Expected Strokes (EV)** per strategy (Aggressive / Balanced / Conservative)
  - **Blow-up Probability**
  - **CaddieScore** (Sharpe-like: reward ÷ risk)
- Outputs per-hole recommendations: **Press** or **Protect**

## Technical Architecture
```
app/
├─ services/minigolfstrategy/
│  ├─ core_service.py
│  ├─ strategy_service.py      # ExecutiveCaddieCalculator
│  └─ clients/golfcourse_api.py
├─ api/v1/endpoints/minigolfstrategy/
│  ├─ core.py
│  ├─ courses.py               # search/details (tee & hole info)
│  └─ strategy.py              # /strategy/caddiealpha
└─ models/golf_models.py
```

## API Contract
**POST** `/api/v1/minigolfstrategy/strategy/caddiealpha`
```json
{
  "course_id": "24636",
  "tee_name": "Blue",
  "gender": "M",
  "risk_budget": 2.5,
  "holes": []
}
```

**Response (excerpt)**
```json
{
  "summary": {
    "caddie_score_total": 4.8,
    "risk_budget_used": 2.3,
    "press_holes": [5, 7, 10],
    "protect_holes": [8, 14, 18]
  },
  "holes": [
    {
      "hole": 8,
      "par": 4,
      "yardage": 420,
      "handicap": 2,
      "recommended": "conservative",
      "explain": "High slope + low handicap → preserve par; press elsewhere."
    }
  ]
}
```

## Frontend (Executive Mode)
- Single clean page with 18-hole bars
- Colors: **Green = Press**, **Red = Protect**
- KPI summary: Risk Budget Used, CaddieScore Total, Press/Protect holes

## Enterprise Readiness
- PII-lite (no player identity required)
- Audit logs + versioned models
- SOC2-friendly design
- SSO-ready (OIDC stub)

## Next Steps
1. Implement `ExecutiveCaddieCalculator` + `/strategy/caddiealpha` endpoint
2. Expose tee/gender + hole details in `/courses/details`
3. Build minimal executive UI (18-hole bar view)
4. Add logging + monitoring for enterprise deployment
