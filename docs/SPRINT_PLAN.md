# EARP Sprint Plan

**Project:** Enterprise AI Reliability Platform v1 (EARP)
**Release:** v0.3.0 HR-ready package
**Owner:** Shannon Bryan Kelly (`coconuthead-Sentinel-core`)
**Working branch:** `release/v0.3.0`
**Framework:** 4 Drive docs + folder-as-context (Interdepartmental Memo,
Persistent Session Reference Guidelines, "the folder is the working context",
15_20_25_min_work_user).

---

## How sprints map to the product backlog

The product backlog (`product_backlog/product_backlog.txt`) has **5 epics**
with **3 stories each**. One epic → one sprint. Each sprint ends with code
pushed, tests green, and a CHANGELOG entry.

| Sprint | Epic | Title                                  | Status       |
|--------|------|----------------------------------------|--------------|
| 0      | —    | Repo handoff, remote wiring, baseline  | ✅ done       |
| 1      | E1   | Evidence Ingestion and Normalization   | ✅ done (shim) |
| 2      | E2   | Reliability Scoring Engine             | 🟢 in progress|
| 3      | E3   | Policy Gate Evaluation                 | ⏳ planned    |
| 4      | E4   | Dashboard and Reporting                | ⏳ planned    |
| 5      | E5   | Security and Compliance                | ⏳ planned    |

---

## Sprint 0 — Repo handoff and baseline (✅ done)

- Added local git remote pointing at the GitHub repo.
- Pushed local `main` to `release/v0.3.0` on GitHub (per CONTRIBUTING rule:
  never push straight to `main`).
- Confirmed local validation: 50/50 integration tests pass, Bicep builds
  clean, frontend builds clean.
- Captured operational truth vs. proposed design in the memory notes.

**Exit criteria met:** code on GitHub, branch tracks `origin/release/v0.3.0`,
framework memory saved.

---

## Sprint 1 — Evidence Ingestion and Normalization (🟢 in progress)

**Epic:** E1 from the product backlog.

### Goals
1. Expose the backlog through the API so the dashboard and CI can see sprint
   status without scraping the text file.
2. Add `CHANGELOG.md` at the project root (required by `RELEASE.md`).
3. Add this sprint plan document.
4. Keep the change small, safe, and reviewable — no schema or auth changes.

### Stories delivered in this sprint
- **E1-S1**: Add `/info/epics` read-only endpoint returning the 5 epics and
  their status.
- **E1-S2**: Land `CHANGELOG.md` at project root with a v0.3.0 entry and an
  Unreleased section.
- **E1-S3**: Land `docs/SPRINT_PLAN.md` (this file).

### Definition of Done
- [x] New endpoint added and wired into `main.py`.
- [x] `CHANGELOG.md` present at project root.
- [x] `docs/SPRINT_PLAN.md` present.
- [ ] Changes committed on `release/v0.3.0` with a conventional-commit message.
- [ ] Branch pushed to `origin/release/v0.3.0`.
- [ ] Shannon reviews and either merges to `main` or asks for a change.

### Out of scope (intentionally)
- Real file ingestion, parsing, or storage of evidence artifacts. Those
  stories move to Sprint 1b or Sprint 2 once Shannon has completed the
  Azure + GitHub auth handoff (see "Blockers" below).

---

## Sprint 2 — Reliability Scoring Engine (🟢 in progress)

**Epic:** E2. Backlog stories: `E2-S1`, `E2-S2`, `E2-S3`.

### Story E2-S1 — Weighted score algorithm implementation (✅ done)

- `POST /reliability/score` endpoint accepts an arbitrary list of
  reliability signals (availability, governance, security posture, etc.),
  each with a value in `[0, 1]` and a weight.
- Returns a weighted 0-100 composite score, a LOW/MEDIUM/HIGH tier, a
  boolean indicating whether the input weights were normalized, and a
  per-NIST-AI-RMF-function breakdown (govern/map/measure/manage).
- Pure-Python math in `services.compute_reliability_score()` — no new
  heavy dependencies.
- 19 integration assertions cover the happy path, NIST breakdown,
  weight normalization, three tier boundaries, and three validation
  failures. Suite runs **81/81**.

### Story E2-S2 — Score explanation service (✅ done)

- `POST /reliability/score/explain` wraps the composite score with a
  structured `explanation` object:
  - per-component contributions (absolute + percent-of-composite),
    sorted highest-first,
  - `top_driver` (largest contributor) and `top_gap` (lowest-value
    component, i.e. biggest upside),
  - `tier_gap` — distance in composite points to the adjacent
    LOW / MEDIUM / HIGH tier boundaries,
  - `weakest_nist_function` / `strongest_nist_function` from the NIST
    AI RMF breakdown,
  - a one-sentence plain-English `recommendation`.
- Pure-Python layer on top of `compute_reliability_score()` — no new
  dependencies.
- 35 integration assertions added (happy path, sort invariants, sum-to-
  composite, LOW / MEDIUM / HIGH tier-gap paths, single-component edge
  case, validation). Suite runs **116/116**.

### Story E2-S3 — Historical trend computation (⏳ next)

- Persist each scoring call (similar to the `ReliabilityComputation`
  table) and expose a `GET /reliability/score/history` endpoint with
  simple trend stats (rolling average, tier transitions).

---

## Sprint 3 — Policy Gate Evaluation (⏳ planned)

**Epic:** E3.

- Add a policy gate that consumes the reliability score and returns
  allow / warn / block with reasons.
- Hook into `/assessments` so each assessment gets a gate decision attached.
- Add integration tests covering allow / warn / block paths.

---

## Sprint 4 — Dashboard and Reporting (⏳ planned)

**Epic:** E4.

- Frontend cards for: reliability score, gate status, epic progress
  (consumes `/info/epics`), recent assessments.
- Exportable HR-review PDF built from the same data.

---

## Sprint 5 — Security and Compliance (⏳ planned)

**Epic:** E5.

- Finalize the `security-scans` workflow: SBOM, dependency scan, secret scan.
- Close any open OWASP Threat Dragon items.
- Produce the NIST AI RMF evidence bundle for HR review.

---

## Blockers that Shannon must clear (outside Claude's control)

These are credential-only steps. Claude cannot log in for Shannon.

1. `gh auth login` — so PRs can be opened from the terminal.
2. `az login` — so Azure resources in `rg-earp-dev-centralus` can be created.
3. Set 5 GitHub Actions secrets:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
   - `AZURE_MANAGED_IDENTITY_ID`
   - `AZURE_KEY_VAULT_URI`
4. Set 3 Key Vault secrets: `jwt-secret`, `database-url`, `redis-url`.

Once items 1–4 are done, Sprint 2 can start deploying to Azure.

---

## Working agreement (per the 4 Drive docs)

- Every response: chunked, bulleted, emoji markers, verified vs. proposed
  separated.
- Edit documentation in this folder only. `_admin_archives/` is immutable.
- Don't confuse operational truth (what runs) with conceptual design (what we
  plan). Verify before claiming done.
