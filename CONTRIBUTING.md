# Contributing to EARP

## Branch model

* `main`      — production. Protected, requires PR + passing CI + CODEOWNERS review.
* `develop`   — integration branch. PRs from `feature/*` merge here first.
* `feature/*` — short-lived feature branches off `develop`.
* `hotfix/*`  — from `main` for emergency fixes.
* `release/*` — stabilisation branches before a tag.

## Local dev checklist (before you open a PR)

```bash
# Backend
cd enterprise_ai_backend
pip install -r requirements.txt
python tests/test_backend.py       # must pass 50/50

# Frontend
cd apps/web
npm install
npm run typecheck
npm run build

# Regenerate OpenAPI spec if you changed any route or schema
cd enterprise_ai_backend
python -c "import json; from app.main import app; \
  open('../libs/schemas/openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
```

## PR rules

1. One logical change per PR.
2. Link an issue or ADR for anything bigger than a typo.
3. Update docs in the same PR as the code.
4. If you change `libs/policy/scoring.py` — add a reason in the PR
   description; CODEOWNERS review is required.
5. If you change the OpenAPI contract — regenerate `libs/schemas/openapi.json`
   or `ci-contracts.yml` will fail.

## Commit messages

Conventional-ish prefixes:

    feat(api): add /ai/anomaly-detect/from-history endpoint
    fix(web): handle 401 on expired token
    chore(ci): pin actions/setup-python@v5
    docs: update deploy guide
    infra(bicep): add Key Vault references

## Coding style

* Python: PEP 8, type hints, ruff-compatible. No bare `except`.
* TypeScript: strict mode is on. Run `npm run typecheck` before pushing.
* FastAPI endpoints always return a typed `response_model`.
* No business logic in route functions — push it into `app/services.py`
  or `libs/policy`.

## Tests

* Every new endpoint needs a test in `enterprise_ai_backend/tests/test_backend.py`.
* Every new policy constant needs a test in `ci-contracts.yml`'s smoke block.

## Security

Never commit `.env`, real JWT secrets, Azure credentials, or customer
data. `security-scans.yml` will fail the PR; see `SECURITY.md` for
responsible disclosure.
