# Changelog

All notable changes to the Enterprise AI Reliability Platform will be
documented in this file.  Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- `POST /reliability/score` endpoint — full reliability and policy scoring (Sprint 2 / Epic E2-S1)
- Deterministic scoring service with SDLC ReliabilityIndex and Readiness Policy composite scores
- NIST AI RMF 1.0 function mapping in every score response (Govern / Map / Measure / Manage)
- Hard-constraint checks: HallucinationRate ≤ 0.03, SafetyViolationRate ≤ 0.01
- Gate outcomes: pass (≥ 0.85), conditional (0.78–0.85), fail (< 0.78 or hard-constraint violation)
- Unit tests for scoring math (100 % branch coverage of scoring service)

## [0.3.0] — 2026-04-19

### Added
- FastAPI application scaffold (`enterprise_ai_backend`)
- `GET /info/epics` — returns the five product-backlog epics
- `GET /info/sprint` — returns current sprint status and roadmap
- `GET /healthz` — liveness probe
- `docs/SPRINT_PLAN.md` — maps epics to sprints
- `pyproject.toml` with dev dependencies (pytest, httpx, ruff)
