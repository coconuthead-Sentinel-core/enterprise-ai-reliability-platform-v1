# Dashboard and Reporting

Sprint 4 adds a local dashboard/reporting slice on top of the existing
reliability, policy, and assessment APIs.

## Backend endpoints

| Endpoint | Auth | Purpose |
| --- | --- | --- |
| `GET /dashboard/summary` | bearer | Role-aware dashboard payload |
| `GET /reports/executive-summary` | bearer | Structured executive summary JSON |
| `GET /reports/executive-summary.pdf` | bearer | Downloadable PDF export |

## Frontend surface

The React workspace now includes:

- Release view
- Security view
- Executive view
- Local sample-data seeding
- PDF export

## Local smoke path

1. Start the backend on `127.0.0.1:8000`
2. Start the frontend on `127.0.0.1:5173`
3. Open the workspace
4. Seed sample data
5. Verify the metrics, epic table, assessment posture, policy history, and
   compliance controls
6. Export the PDF and confirm the file downloads
