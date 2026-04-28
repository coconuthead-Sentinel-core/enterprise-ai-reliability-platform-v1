# Portfolio Brief — Enterprise AI Reliability Platform v1 (EARP)

> **One-page recruiter overview.** Architecture detail in [`../README.md`](../README.md). Polish-pass changelog in [`../POLISH_NOTES.md`](../POLISH_NOTES.md).

## TL;DR

**Production-grade platform** for scoring and monitoring AI systems against the NIST AI Risk Management Framework (GOVERN / MAP / MEASURE / MANAGE). Real FastAPI · real bcrypt + JWT · real SQLite · real scikit-learn `IsolationForest` for anomaly detection · OpenAPI 3.1 contract · React 18 + TypeScript + Vite dashboard · Docker compose for local · Azure bicep for deployment. **378/378 integration assertions passing on v0.3.0** (validated 2026-04-21). The strongest senior-tier portfolio piece in the trilogy.

## Role demonstrated

**AI Reliability Engineer / AI Compliance Architect / Senior Backend Engineer** — NIST AI RMF compliance implementation, anomaly-detection ML integration, full-stack reliability engineering with policy gating and audit history.

## What this project demonstrates (for hiring review)

| Capability | Evidence |
|---|---|
| **NIST AI RMF compliance implementation** | `libs/policy/` with explicit GOVERN / MAP / MEASURE / MANAGE scoring policy; `NIST AI RMF Folder Completion Plan` directory; explicit framework alignment, not retrofitted compliance |
| **Production test discipline** | **378 / 378 integration assertions passing** on v0.3.0 — this is senior-engineering-grade test coverage |
| **Real ML integration** | scikit-learn `IsolationForest` running real anomaly detection — not mock |
| **Real auth** | bcrypt for password hashing + JWT for session tokens — not stubs |
| **Real persistence** | SQLite with documented schema; production-graduated, not in-memory |
| **OpenAPI 3.1 contract** | `libs/schemas/` exports the contract directly from FastAPI — single source of truth |
| **Modern frontend** | React 18 + TypeScript + Vite — current 2026 stack, not legacy |
| **Container deployment** | `infra/docker/` for local + `infra/bicep/` for Azure Container Apps — multi-target deploy |
| **Reliability engineering math** | Reliability scoring, policy gating, audit history — the actual compliance-engineering work, not paperwork |
| **Governance artifacts complete** | `decision_log_adr/` · `data_governance_and_privacy_plan/` · `ga_hardening_compliance_launch/` · `go_no_go_checklist/` · `incident_response_runbook/` · `architecture_and_api_contracts/` · `discovery_and_problem_definition/` — every senior-SDLC artifact present |
| **Release discipline** | `CHANGELOG.md` + `RELEASE.md` + `SECURITY.md` + `CONTRIBUTING.md` + `LICENSE` — all present |

## Honest scope statement

**Status (per README):** v0.3.0, full local build validated 2026-04-21. Real FastAPI, real bcrypt+JWT, real SQLite, real `IsolationForest`. **378/378 integration assertions passing.** Repo docs, contracts, and release packaging are current. Azure credential provisioning remains an external prerequisite intentionally excluded from the current work cycle.

That's a recruiter-defensible, senior-engineer-honest scope statement. Production-graduated locally; Azure-ready; deployment-credentialing is the next gate — not a hidden gap.

## Why this is the strongest senior-tier pitch in the portfolio

| Other portfolio pieces | This project |
|---|---|
| Sentinel-Forge (LIB-PROJ-001) — production patterns + Stripe billing | EARP — production patterns + **NIST compliance framework** |
| Forge-Stack-A1 (LIB-PROJ-002) — three-tier MVP scaffold | EARP — three-tier production-graduated codebase |
| Quantum Nexus Forge (LIB-PROJ-003) — proof-of-concept MVP | EARP — production v0.3.0 with 378-test coverage |
| Sovereign Forge (LIB-PROJ-004) — multi-platform gateway | EARP — full SDLC governance tree |

EARP is the project to **lead with for senior reliability-engineering and AI-compliance roles**. The NIST AI RMF scoring policy is rare-skill-premium territory — most candidates know the framework name; few have built systems that score against it.

## Differentiators worth naming for HR

1. **NIST AI RMF as live scoring policy, not just documentation** — the framework is encoded in `libs/policy/`, scored by the API, audited in history
2. **378/378 integration assertions** — senior-tier test discipline; this is what production hiring committees ask for
3. **Reliability-engineering math in the codebase** — not just "we have monitoring" but actual scoring algorithms with `IsolationForest` anomaly detection
4. **Decision-log ADR discipline** — the `decision_log_adr/` directory shows architecture decisions are documented at senior-engineer standard
5. **Multi-target deployment** — same code runs Docker compose locally and Azure Container Apps via bicep

## Author

**Shannon Brian Kelly** — Healthcare CNA → AI Systems Developer career transition.
Built in collaboration with Claude AI (Anthropic).

## License

See `LICENSE` at project root.

---

*Portfolio Brief v001 — 2026-04-28. Generated during the multi-project portfolio sprint. Of the 6 portfolio pieces, this is the lead artifact for senior-tier AI reliability / compliance role applications.*
