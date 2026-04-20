# EARP developer docs index

This folder is the engineering on-ramp for the repo. The larger SDLC and
compliance paperwork still lives at the repo root in dedicated folders.

## Code and delivery docs

| Area | Location | Read this first |
| --- | --- | --- |
| API source | `enterprise_ai_backend/` | `enterprise_ai_backend/README.md` |
| Web source | `apps/web/` | `apps/web/README.md` |
| Shared policy | `libs/policy/scoring.py` | `libs/policy/README.md` |
| API contract | `libs/schemas/openapi.json` | `libs/schemas/README.md` |
| Sprint truth | `docs/SPRINT_PLAN.md` | this file after code review |
| Go/no-go | `docs/go-no-go.md` | release readiness |
| Release evidence | `docs/release-evidence.md` | exact validation and blocker log |
| Dashboard/reporting | `docs/dashboard-reporting.md` | Sprint 4 surface |
| Compliance evidence bundle | `docs/security-compliance-evidence-bundle.md` | Sprint 5 local slice |

## SDLC paperwork at repo root

| Deliverable | Folder |
| --- | --- |
| Project charter | `project_charter/` |
| Discovery + problem definition | `discovery_and_problem_definition/` |
| Market research + use cases | `market_research_and_use_cases/` |
| Requirements + PRD baseline | `requirements_and_prd_baseline/` |
| Architecture + API contracts | `architecture_and_api_contracts/` |
| Decision log (ADRs) | `decision_log_adr/` |
| Product backlog | `product_backlog/` |
| Risk register | `risk_register/` |
| Security + compliance plan | `security_and_compliance_plan/` |
| Data governance + privacy plan | `data_governance_and_privacy_plan/` |
| Test strategy + test plan | `test_strategy_and_test_plan/` |
| Release plan | `release_plan/` |
| MVP - core platform build | `mvp_core_platform_build/` |
| MVP - readiness engine + gates | `mvp_readiness_engine_release_gates/` |
| MVP - dashboard + integrations + testing | `mvp_dashboard_integrations_testing/` |
| Pilot scorecard | `pilot_scorecard_template/` |
| Pilot execution + feedback | `pilot_execution_feedback/` |
| GA hardening, compliance, launch | `ga_hardening_compliance_launch/` |
| Go/no-go checklist | `go_no_go_checklist/` |
| KPI dashboard definition | `kpi_dashboard_definition/` |
| Incident response runbook | `incident_response_runbook/` |
| Maintenance + operating plan | `maintenance_and_operating_plan/` |
| NIST AI RMF folder completion plan | `NIST AI RMF Folder Completion Plan/` |
| Azure reference architecture | `Azure/Azure.txt` |
| Monorepo + CI/CD spec | `GitHub documentation/GitHub documentation.txt` |
| Top-level SDLC | `Project software development life cycle..txt` |

## How the code maps to the paperwork

| Paperwork artifact | Implemented in |
| --- | --- |
| NIST AI RMF scoring policy | `libs/policy/scoring.py` |
| Architecture + API contracts | `libs/schemas/openapi.json` |
| Test strategy | `enterprise_ai_backend/tests/test_backend.py` (313 assertions) |
| Release plan | `RELEASE.md` + `.github/workflows/release.yml` |
| Incident response runbook | `incident_response_runbook/` + rollback steps in `RELEASE.md` |
| Security + compliance plan | `SECURITY.md` + `.github/workflows/security-scans.yml` |
| Azure reference architecture | `infra/bicep/main.bicep` |
| Go/no-go checklist | `docs/go-no-go.md` |
| HR reviewer runbook | `docs/hr-review-guide.md` |
| Release evidence | `docs/release-evidence.md` |
