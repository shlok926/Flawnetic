# 04 — Database Schema

## Entity Overview
```
users ──< projects ──< scan_runs ──< pages ──< findings ──< evidence
                                          │
                                          └──< test_cases (functional engine only)
```

## Tables

### `users`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| email | text unique | |
| password_hash | text | |
| name | text | |
| role | enum(admin, member) | |
| created_at | timestamp | |

### `projects`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK → users.id | |
| name | text | e.g. "Client A — Marketing Site" |
| base_url | text | root URL to crawl |
| created_at | timestamp | |

### `scan_runs`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| project_id | uuid FK → projects.id | |
| status | enum(queued, crawling, testing, generating_report, done, failed) | |
| started_at | timestamp | |
| finished_at | timestamp | nullable |
| config | jsonb | max_pages, max_depth, modules_enabled (functional/security/a11y/visual/perf), browsers_to_test |
| summary | jsonb | total_pages, total_findings, severity_counts — denormalized for fast dashboard reads |

### `pages`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| scan_run_id | uuid FK → scan_runs.id | |
| url | text | |
| title | text | |
| discovered_via | text | parent URL / "root" |
| http_status | int | |
| screenshot_url | text | baseline screenshot for this page in this run |

### `test_cases` (functional engine — also doubles as the "RTM" source)
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| page_id | uuid FK → pages.id | |
| element_selector | text | |
| element_type | text | input, button, dropdown, checkbox, link |
| test_type | text | positive, negative_empty, negative_special_chars, negative_overflow, negative_numeric_only, etc. |
| input_value | text | what was actually entered/clicked |
| expected_result | text | |
| actual_result | text | |
| passed | boolean | |

### `findings` (the unified bug schema — matches `Finding` JSON in `02-ARCHITECTURE.md`)
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| scan_run_id | uuid FK → scan_runs.id | |
| page_id | uuid FK → pages.id | nullable (some findings are site-wide, e.g. missing security header) |
| test_case_id | uuid FK → test_cases.id | nullable, only for functional findings |
| module | enum(functional, security, accessibility, visual, usability) | |
| title | text | |
| description | text | |
| steps_to_reproduce | jsonb | array of strings |
| expected_result | text | |
| actual_result | text | |
| severity | enum(critical, high, medium, low) | |
| priority | enum(high, medium, low) | |
| root_cause_hint | text | AI-generated, nullable |
| occurrence_count | int | how many pages/instances this same bug appeared on (dedupe count) |
| detected_at | timestamp | |

### `evidence`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| finding_id | uuid FK → findings.id | |
| type | enum(screenshot, dom_snapshot, console_log, network_har, video_trace) | |
| storage_url | text | S3/MinIO object URL | |
| created_at | timestamp | |

### `reports`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| scan_run_id | uuid FK → scan_runs.id | |
| pdf_url | text | final generated report file |
| generated_at | timestamp | |

## Indexing notes
- Index `findings(scan_run_id, severity)` — dashboard filters by severity constantly
- Index `pages(scan_run_id, url)` — crawler dedupe check (avoid re-visiting same URL)
- `scan_runs.summary` denormalized JSONB avoids expensive COUNT() aggregations on every dashboard load
