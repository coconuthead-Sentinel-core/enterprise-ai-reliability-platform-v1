# Security policy

## Supported versions

Only the latest `v0.x` line is supported while the platform is pre-1.0.

| Version  | Supported |
|----------|-----------|
| 0.3.x    | ✅        |
| < 0.3    | ❌        |

## Reporting a vulnerability

Please **do not open a public GitHub issue** for security bugs.

Email the project owner privately with:

* A description of the issue
* Steps to reproduce (or a proof of concept)
* The commit SHA or version affected
* Your disclosure timeline expectation

You'll get an acknowledgement within **72 hours** and a remediation
plan within **7 days** for critical issues. We follow 90-day
coordinated disclosure by default.

## What's in scope

* `enterprise_ai_backend/` (FastAPI application)
* `apps/web/` (React frontend)
* `libs/policy/` (scoring policy)
* `infra/bicep/` (Azure deployment)
* `.github/workflows/` (CI/CD)

## Hardening in place

| Control | Where |
|---------|-------|
| Password hashing | `bcrypt` with cost 12, 72-byte pre-truncation (`app/security.py`) |
| Token format | HS256 JWT with expiry, iat, sub (`app/security.py`) |
| Secret management | Azure Key Vault via managed identity (`infra/bicep/main.bicep`) |
| Dependency scanning | `pip-audit`, `npm audit` (`security-scans.yml`) |
| Static analysis | CodeQL for Python + JS (`security-scans.yml`) |
| Secret scanning | `gitleaks` on every PR (`security-scans.yml`) |
| CORS | Configurable allow-list via `CORS_ORIGINS` env var |
| HTTPS | Enforced by Azure Container Apps ingress |
| Least privilege | User-assigned managed identity with Key Vault Secrets User only |

## Known limitations (v0.3.0)

* No rate limiting on `/auth/login` — add `slowapi` before public beta.
* No refresh tokens — access tokens expire after 60 min and users must
  re-authenticate.
* `JWT_SECRET` rotation requires a rolling deploy; no in-flight rotation.
