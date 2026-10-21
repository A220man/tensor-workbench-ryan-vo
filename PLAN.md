# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

scan-improvement

## Roadmap

### project-skeleton — Project Skeleton with FastAPI/React and Core Build Workflow

Status: done

Acceptance:
- FastAPI backend runs with health endpoint
- React frontend builds and serves dashboard
- Docker Compose starts backend, frontend, and Keycloak
- Backend lists SwiftPM projects from workspace directory
- Frontend displays project list with build status
- Backend tests pass (pytest)
- Frontend typecheck and tests pass (npm run build, npm test)

Implementation: `backend/app/main.py`, `backend/app/api/health.py`, `backend/app/api/version.py`, `backend/app/api/projects.py`, `backend/app/services/project_discovery.py`, `backend/app/models/project.py`, `backend/app/models/base.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/api/client.ts`, `frontend/src/api/types.ts`, `frontend/src/App.tsx`, `frontend/src/main.tsx`

Tests: `backend/tests/test_health.py`, `backend/tests/test_projects.py`, `backend/tests/test_project_discovery.py`, `frontend/src/pages/__tests__/Dashboard.test.tsx`, `frontend/src/components/ui/__tests__/ui.test.tsx`

### scan-improvement — Scan Workspace Added/Updated Tracking

Status: done

Acceptance:
- Scan endpoint returns accurate added/updated project counts
- Service tracks whether each discovered project is new or updated
- Tests verify added/updated counts

Implementation: `backend/app/services/project_discovery.py`, `backend/app/api/projects.py`

Tests: `backend/tests/test_project_discovery.py`

### swiftpm-build — SwiftPM Build Orchestration

Status: planned

Acceptance:
- Backend can trigger `swift build` for a selected project
- Build logs streamed to frontend via SSE/WebSocket
- Build artifacts (binary, .app bundle) listed after success
- Cross-compilation target selection (device/simulator)

### device-management — iOS Device Connection and Deployment

Status: planned

Acceptance:
- Backend detects connected iOS devices via usbmuxd/ideviceinstaller
- Frontend shows device list with connection status
- Deploy .app bundle to selected device
- Address 'stuck on Connecting' with proper logging/timeout handling

### sdk-management — Darwin SDK Installation and Status

Status: planned

Acceptance:
- Backend can download/install Darwin SDK from Apple
- SDK status endpoint shows installed versions
- Frontend SDK manager with install/remove actions

### apple-auth — Apple Developer Authentication

Status: planned

Acceptance:
- OIDC login with Keycloak (configured for Apple ID broker)
- 2FA handling with proper timeout/fallback
- App Store Connect API token management
- Capability registration (WeatherKit, etc.)

### xcode-project-import — Xcode Project Import/Conversion

Status: planned

Acceptance:
- Parse .xcodeproj/.xcworkspace files
- Convert to SwiftPM Package.swift
- Preserve targets, schemes, build settings

### simulator-support — iOS Simulator on Linux/Windows

Status: planned

Acceptance:
- Research feasibility document
- QEMU/KVM-based approach or remote macOS runner integration
- Proof-of-concept for headless simulator

