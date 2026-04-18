# apps/web — EARP frontend (React + TypeScript + Vite)

React 18 + TypeScript + Vite. Talks to the FastAPI backend at `apps/api`
(which is the running code in `../../enterprise_ai_backend`).

## Scripts

```bash
npm install
npm run dev         # http://127.0.0.1:5173
npm run build       # production build -> dist/
npm run typecheck
```

## Dev proxy

`vite.config.ts` proxies `/api/*` to `http://127.0.0.1:8000/*`, so the same
fetch URL works in dev and prod without CORS juggling.

## Prod

Set `VITE_API_BASE` to the deployed API origin (e.g.
`https://ca-earp-prod.eastus.azurecontainerapps.io`) at build time.

## Screens

1. **Auth** — login/register against `/auth/register` and `/auth/login`
2. **Reliability** — POST to `/reliability/compute` with MTBF/MTTR/mission time
3. **History** — GET `/reliability/history`
4. **Anomaly detection** — GET `/ai/anomaly-detect/from-history` (real
   scikit-learn IsolationForest)
