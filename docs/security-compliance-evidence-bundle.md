# Security and Compliance Evidence Bundle

Sprint 5 local work adds a repo-backed evidence bundle to the executive summary.

## Current controls

1. `CTRL-01` Authentication and Role Boundary
2. `CTRL-02` CI Security Scanning
3. `CTRL-03` Audit Logging and Release Traceability
4. `CTRL-04` Release Governance
5. `CTRL-05` Retention and Legal Hold

## Current status

- Implemented: separated release approvals for Security Lead and Compliance Lead
- Implemented: append-only hash-chained audit ledger with verification
- Implemented: local retention policy and legal-hold controls
- Implemented: CI security scanning
- Partial: auth boundaries, audit traceability, release governance, cloud retention enforcement

## Open gaps

- Azure deployment secrets and live smoke tests
- External immutable storage for the audit ledger
- Cloud lifecycle policy or scheduled retention enforcement

## Delivery surfaces

The evidence bundle is available through:

- `GET /reports/executive-summary`
- `GET /reports/executive-summary.pdf`
- `GET /audit/history`
- `GET /audit/verify`
- `GET /compliance/retention/policy`
- `GET /compliance/retention/status`
- `POST /compliance/legal-holds`
