# apps/web - EARP frontend (React + TypeScript + Vite)

React 18 + TypeScript + Vite dashboard workspace for the Enterprise AI
Reliability Platform. It talks to the live FastAPI backend in
`../../enterprise_ai_backend`.

## Scripts

```bash
npm install
npm run dev         # http://127.0.0.1:5173
npm run build       # production build -> dist/
npm run typecheck
```

## Dev proxy

`vite.config.ts` proxies `/api/*` to `http://127.0.0.1:8000/*`, so the same
fetch URLs work in dev and prod without CORS churn.

## Product surface

The app provides:

1. Workspace sign-in / register flow
2. Release dashboard view
3. Security dashboard view
4. Executive summary view
5. Local sample-data seeding
6. PDF export via `/reports/executive-summary.pdf`

## Prod

Set `VITE_API_BASE` to the deployed API origin at build time.
