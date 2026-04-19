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
- `docs/SPRINT_PLAN.md` mapping the product backlog (E1–E5) to a 5-sprint
  delivery roadmap.
- `CHANGELOG.md` at the project root (this file).

### Changed
- Registered the new `info` router in `enterprise_ai_backend/app/main.py`.

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
