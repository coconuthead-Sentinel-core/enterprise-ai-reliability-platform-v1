# libs/schemas — shared OpenAPI contract

The FastAPI backend in `apps/api` auto-generates an OpenAPI 3.1 spec
at runtime. Exporting it to `openapi.json` here makes the contract
consumable by the web app, future mobile clients, and CI.

## Regenerate

From the repo root:

```bash
cd enterprise_ai_backend
python -c "import json; from app.main import app; \
  open('../libs/schemas/openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
```

(The `ci-contracts.yml` workflow runs this and fails the build on any
unreviewed diff.)

## Files

* `openapi.json` — full OpenAPI 3.1 contract (generated)

## Consumers

* `apps/web` — typed client (hand-written today, can be codegen-ed from
  `openapi.json` via `openapi-typescript` in the future)
* `libs/policy` — scoring math shared between API and UI
