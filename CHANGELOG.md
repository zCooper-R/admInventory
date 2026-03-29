# Changelog

All notable changes to **admInventory** are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

> Features planned for the next release.

---

## [0.1.0] — 2026-03-29

First public release. Fully functional MVP covering PC inventory management for
multi-branch organisations.

### Added

**Core inventory**
- `Device` model with PC/Laptop/Printer/Other types, full field set
  (CPU, RAM, storage, OS, serial number, purchase date, status).
- `Organization` → `Location` hierarchy for multi-branch support.
- Custom `User` model with `admin / manager / user` roles and optional
  `Location` FK for role-based data scoping (managers see only their branch).
- `SystemSettings` singleton model — configurable thresholds and branding
  without redeployment.

**Dashboard & UI**
- Modern Bootstrap 5 dashboard with KPI cards and Chart.js charts
  (status distribution, top locations).
- Responsive PC list with zebra stripes, column sorting, HTMX-powered
  filtering and pagination — zero full-page reloads.
- HTMX modals for PC create / edit / delete.
- Dark / light theme toggle persisted in `localStorage`.
- Mobile-first responsive layout: sidebar drawer, table → card transform.
- Real-time critical-PC badge (HTMX polling every 60 s + OOB swaps).
- Web-based system settings page (admin only).
- Bootstrap `needs-validation` client-side form validation with
  `invalid-feedback` messages.

**Excel import / export**
- Excel import via `pandas` / `openpyxl` with error logging (`ImportLog`).
- Excel export for all PCs with timestamped filename.
- Downloadable import template with sample rows.

**Budget / replacement planning**
- `build_budget_report()` — assesses every PC by RAM, age, storage type,
  and operational status.
- Severity levels: `critical` / `medium` / `low`.
- Per-location cost breakdown with total replacement budget.
- Shareable URL: `?price=N` overrides the default price from `SystemSettings`.
- 5-minute cache for the default-price report; auto-invalidated on Device change.

**Agent (automated data collection)**
- `POST /api/v1/devices/sync/` — unauthenticated endpoint secured by
  `X-Api-Key` (constant-time `hmac.compare_digest`).
- PowerShell agent (`scripts/agent.ps1`) reads hardware via WMI and posts
  to the sync endpoint.
- Python agent (`scripts/agent.py`) — cross-platform alternative.
- `install_agent.bat` — one-click scheduled-task installer for IT staff.

**REST API**
- DRF ViewSets for `Device`, `Organization`, `Location`.
- Filtering, search, ordering, pagination.
- `GET /api/version/` — application version endpoint.

**Developer experience**
- Split settings: `base.py` / `dev.py` / `prod.py`.
- Docker Compose for development; `docker-compose.prod.yml` for production
  (Gunicorn + WhiteNoise).
- `pytest` + `factory-boy` test suite (inventory, locations, web views,
  import/export, settings, critical badge, template download).
- GitHub Actions CI: pytest, flake8, migration check.
- Pre-commit hooks: `black`, `isort`, `flake8`.
- `create_demo_data` management command (reads `fixtures/demo_data.json`).
- `create_sample_excel` management command for import template generation.

### Architecture

```
backend/
├── config/           settings, urls, version, api_router
├── apps/
│   ├── users/        custom User model, roles
│   ├── locations/    Organization, Location
│   ├── inventory/    Device, SystemSettings, views/, services/
│   └── import_export/ ImportLog, pandas import service
├── templates/        Django templates (Bootstrap 5 + HTMX)
├── static/           CSS (custom properties, dark mode) + JS
└── tests/            pytest test suite
```

---

## Release checklist

```
1. Bump VERSION + RELEASE_DATE in backend/config/version.py
2. Add entry to CHANGELOG.md
3. git add -A
4. git commit -m "release: vX.Y.Z"
5. git tag vX.Y.Z
6. git push origin main --tags
```
