# Security and Compliance Evidence Bundle

Sprint 5 local work adds a repo-backed evidence bundle to the executive summary.

## Current controls

1. `CTRL-01` Authentication and Role Boundary
2. `CTRL-02` CI Security Scanning
3. `CTRL-03` Audit Logging and Release Traceability
4. `CTRL-04` Release Governance
5. `CTRL-05` Retention and Legal Hold

## Current status

- Implemented: CI security scanning
- Partial: auth boundaries, audit traceability, release governance
- Planned: retention and legal hold automation

## Open gaps

- Azure deployment secrets and live smoke tests
- Stronger approval separation than the current user/admin split
- Tamper-evident or immutable audit storage
- Runtime retention and legal-hold enforcement

## Delivery surfaces

The evidence bundle is available through:

- `GET /reports/executive-summary`
- `GET /reports/executive-summary.pdf`
