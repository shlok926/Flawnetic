# 05 — API Specification (REST)

Base URL: `/api/v1`
Auth: Bearer JWT (`Authorization: Bearer <token>`)

## Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Returns JWT |

## Projects
| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects` | List user's projects |
| POST | `/projects` | Create project `{ name, base_url }` |
| GET | `/projects/{id}` | Project details |
| DELETE | `/projects/{id}` | Delete project |

## Scan Runs
| Method | Endpoint | Description |
|---|---|---|
| POST | `/projects/{id}/scans` | Kick off a new scan. Body: `{ max_pages, max_depth, modules: ["functional","security","accessibility","visual","usability"], browsers: ["chromium","firefox","webkit"] }` |
| GET | `/scans/{run_id}` | Get run status + summary |
| GET | `/scans/{run_id}/live` | WebSocket/SSE stream of live crawl progress (page-by-page) |
| POST | `/scans/{run_id}/cancel` | Stop a running scan |
| GET | `/scans/{run_id}/pages` | List discovered pages |
| GET | `/scans/{run_id}/findings` | List findings, filterable via query params: `?severity=critical&module=security` |
| GET | `/findings/{finding_id}` | Single finding detail with evidence URLs |

## Reports
| Method | Endpoint | Description |
|---|---|---|
| POST | `/scans/{run_id}/report` | Trigger report generation (if not auto-generated at scan completion) |
| GET | `/scans/{run_id}/report` | Returns report metadata + PDF download URL |
| GET | `/reports/{report_id}/download` | Direct PDF file download |

## Integrations (Phase 3)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/scans/{run_id}/export/jira` | Push all findings as Jira issues |
| POST | `/scans/{run_id}/export/trello` | Push all findings as Trello cards |
| POST | `/projects/{id}/webhooks` | Register a webhook (e.g., Slack notify on scan completion) |

## CLI-facing endpoint (for CI/CD use, Phase 3)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/ci/scans` | Same as scan creation but synchronous-friendly: polls until done or times out, returns pass/fail + summary JSON (for failing a CI build on critical findings) |

## Example: kick off a scan
```http
POST /api/v1/projects/8f3e.../scans
Content-Type: application/json
Authorization: Bearer <token>

{
  "max_pages": 50,
  "max_depth": 4,
  "modules": ["functional", "security", "accessibility", "visual", "usability"],
  "browsers": ["chromium", "webkit"]
}
```
Response:
```json
{
  "run_id": "a1b2c3...",
  "status": "queued"
}
```

## Example: finding object returned by `/scans/{run_id}/findings`
See the `Finding` schema defined in `02-ARCHITECTURE.md` — this is the exact shape returned by this endpoint, with evidence URLs pre-signed for temporary access.
