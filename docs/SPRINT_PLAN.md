# Sprint Plan

Maps the five product-backlog epics to implementation sprints.

| Sprint | Epic | Status | Summary |
|--------|------|--------|---------|
| 0 | — | ✅ Done | Initial HR-ready EARP release package on GitHub |
| 1 | E1 (slice) | ✅ Done | Info endpoints (`/info/epics`, `/info/sprint`) + sprint plan |
| 2 | E2 | 🟢 In Progress | Reliability Scoring Engine — `POST /reliability/score` |
| 3 | E3 | ⏳ Planned | Policy Gate Evaluation — rule parser + gate endpoint |
| 4 | E4 | ⏳ Planned | Dashboard and Reporting — role-based views + export |
| 5 | E5 | ⏳ Planned | Security and Compliance — RBAC + immutable audit log |

## Sprint 0 — Initial Release Package

- Mirrored documentation tree to GitHub
- Created `release/v0.3.0` branch

## Sprint 1 — Info Endpoints

- `GET /info/epics` returns the 5 backlog epics
- `GET /info/sprint` returns sprint roadmap with status
- `docs/SPRINT_PLAN.md` created
- `CHANGELOG.md` created

## Sprint 2 — Reliability Scoring Engine (Epic E2-S1)

- `POST /reliability/score` endpoint
- Wires SDLC ReliabilityIndex equation:
  `RI = 0.30×Groundedness + 0.25×TaskSuccess + 0.20×PolicyCompliance + 0.15×LatencySLO + 0.10×Availability`
- Wires Readiness Policy Score equation:
  `PS = 0.30×groundedness + 0.20×task_success + 0.15×prompt_robustness + 0.15×safety + 0.10×latency_slo + 0.10×audit`
- Gate outcomes: pass / conditional / fail
- Hard-constraint enforcement (HallucinationRate, SafetyViolationRate)
- NIST AI RMF 1.0 mapping in every response
- Unit tests for scoring math

## Sprint 3 — Policy Gate Evaluation (Epic E3)

- Rule parser and validator
- `POST /gates/evaluate` endpoint
- Exception approval workflow

## Sprint 4 — Dashboard and Reporting (Epic E4)

- Role-based dashboard views
- Compliance report export
- Executive KPI summary page

## Sprint 5 — Security and Compliance (Epic E5)

- RBAC and approval separation
- Immutable audit logging
- Retention and legal hold configuration
