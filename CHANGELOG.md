# Changelog

All notable changes to the Enterprise AI Reliability Platform (EARP) will be
documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `GET /info/epics` endpoint exposing the 5 product backlog epics and their
  current status, so the dashboard and CI can surface sprint progress without
  reading the backlog file directly.
- `GET /info/sprint` endpoint returning the current sprint summary
  (`current_sprint`, `total_sprints`, `release`, `branch`).
- `docs/SPRINT_PLAN.md` mapping the product backlog (E1–E5) to a 5-sprint
  delivery roadmap.
- `CHANGELOG.md` at the project root (this file).
- `LICENSE` at the project root — proprietary / pre-commercial notice; will be
  replaced with a standard OSS or commercial license at v1.0.0.
- `Azure/README.md` explaining the three-way Azure layout (`Azure/` for
  planning prose, `.azure/` for live deployment status, `infra/bicep/` for IaC).
- Integration tests for the new `/info/epics` and `/info/sprint` endpoints
  (12 new assertions — suite now runs **62/62**, up from 50/50).

### Changed
- Registered the new `info` router in `enterprise_ai_backend/app/main.py`.
- `README.md` updated from "50/50 integration assertions" to the new count.

### Removed
- Untracked four stale legacy draft folders from git (files remain on the
  author's disk, but are no longer part of the repository):
  - `Back in/` (old backend iterations, already in `.gitignore`)
  - `Front end/` (early draft text)
  - `Middle layer/` (early draft text)
  - `Enterprise readability AI Platform v1 Artificial Intelligence/` (misspelled
    legacy folder containing a duplicate NIST RMF PDF)
- `.gitignore` extended to prevent these legacy folders from being re-added.

## [0.3.0] - 2026-04-19

### Added
- Initial HR-ready release package of the Enterprise AI Reliability Platform.
- FastAPI backend with routers for `health`, `auth`, `reliability`,
  `assessments`, `ai`, and `hash`.
- React 18 + TypeScript + Vite frontend shell.
- Docker Compose dev stack.
- Azure Container Apps + Bicep infrastructure-as-code under `infra/`.
- GitHub Actions workflows: `ci-api`, `ci-web`, `ci-contracts`,
  `security-scans`, and `release`.
- Product backlog (`product_backlog/product_backlog.txt`) with 5 epics and
  15 stories.
- Documentation set under `docs/` including HR review guide, go/no-go
  checklist, and release evidence template.

### Security
- bcrypt password hashing and python-jose JWT issuance for auth.
- Baseline OWASP / dependency scanning via the `security-scans` workflow.

[Unreleased]: https://github.com/coconuthead-Sentinel-core/enterprise-ai-reliability-platform-v1/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/coconuthead-Sentinel-core/enterprise-ai-reliability-platform-v1/releases/tag/v0.3.0
