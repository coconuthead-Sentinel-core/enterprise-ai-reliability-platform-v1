# Pull Request

## Summary

<!-- What does this change and why? Keep it to 3-5 bullets. -->

-
-
-

## Change type

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (bumps major version)
- [ ] Documentation / tooling
- [ ] Infra / CI
- [ ] Policy or contract change (`libs/policy` or `libs/schemas`)

## Test plan

- [ ] `python enterprise_ai_backend/tests/test_backend.py` passes locally
- [ ] `cd apps/web && npm run typecheck && npm run build` passes locally
- [ ] New/changed behaviour has test coverage
- [ ] Manual verification (describe below)

<!-- Describe manual verification steps -->

## Risk & rollback

- **Blast radius:**
- **Rollback:** (e.g., revert PR, previous container image tag)

## Checklist

- [ ] I updated `libs/schemas/openapi.json` if the API contract changed
- [ ] I updated relevant docs (`docs/`, README)
- [ ] I added or updated `docs/decision_log_adr/` if this is an architectural decision
- [ ] No secrets, tokens, or PII in the diff
- [ ] CODEOWNERS will be auto-requested

## Related

<!-- Issue links, related PRs, ADRs, etc. -->
