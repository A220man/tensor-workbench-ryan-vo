# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-10-31

### Enhanced
- Scan workspace endpoint (`POST /api/projects/scan`) now returns `added_projects` and `updated_projects` lists with project names for better visibility
- Scan endpoint uses FastAPI `BackgroundTasks` for improved responsiveness during long scans
- Targets and dependencies parsing now handles both legacy string arrays and new object formats for backward compatibility

### Fixed
- Default pagination limit changed from 20 to 50 to match test expectations
- Targets and dependencies correctly deserialize from SQLAlchemy JSON columns

### Testing
- Updated `test_get_project_by_id` to validate structured targets/dependencies response format
- All 14 backend tests pass, 19 frontend tests pass

## [1.1.0] - 2026-10-21

### Fixed
- Scan workspace endpoint (`POST /api/projects/scan`) now returns accurate `added` and `updated` project counts instead of always zero
- Project discovery service (`scan_workspace`) tracks whether each discovered project is newly created or an existing record update

### Testing
- Added `test_scan_workspace_updates_existing_projects` to verify re-scanning returns updated=1 for modified projects
- All 14 backend tests pass, 19 frontend tests pass

## [1.0.0] - 2026-10-14

### Added
- Initial project skeleton with FastAPI backend and React frontend
- Project discovery service: scans workspace for SwiftPM `Package.swift` files
- REST API endpoints:
  - `GET /api/health` - health check with database connectivity
  - `GET /api/version` - application version information
  - `GET /api/projects` - paginated project listing with filtering
  - `GET /api/projects/{id}` - single project details
  - `POST /api/projects/scan` - trigger workspace scan
- Database models: Project, Build, Device, SDK with SQLAlchemy + SQLite
- Frontend dashboard with:
  - Project table with sorting, pagination
  - Project status badges (valid/invalid/building/failed/success)
  - Build status display
  - Scan workspace action
  - Loading, error, and empty states
- Docker Compose orchestration: backend, frontend, Keycloak, PostgreSQL
- Keycloak realm import with OIDC client, roles (admin/operator/viewer), Apple ID identity broker
- Authentication scaffold (OIDC authorization code + PKCE)
- Comprehensive test suite:
  - Backend: 8 pytest tests (health, version, projects API, project discovery)
  - Frontend: 3 vitest test suites (UI components, Dashboard page)
- MIT License, README with architecture diagram, API reference, workflows

### Infrastructure
- Backend Dockerfile (Python 3.12, non-root user, healthcheck)
- Frontend Dockerfile (multi-stage: Node 24 builder → nginx)
- nginx config with SPA fallback and API proxy
- .env.example with all configuration variables
- pyproject.toml with pinned dependencies
- .gitignore excluding secrets, venv, node_modules, build artifacts

### Security
- Demo mode restricted to localhost (refuses in production)
- OIDC tokens stored in memory only (SPA)
- HttpOnly SameSite cookies for backend sessions (planned)
- No hardcoded secrets or credentials
