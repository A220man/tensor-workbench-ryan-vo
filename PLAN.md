# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

project-skeleton

## Roadmap

### project-skeleton — Project Skeleton with FastAPI/React and Core Build Workflow

Status: in_progress

Acceptance:
- FastAPI backend runs with health endpoint
- React frontend builds and serves dashboard
- Docker Compose starts backend, frontend, and Keycloak
- Backend lists SwiftPM projects from workspace directory
- Frontend displays project list with build status
- Backend tests pass (pytest)
- Frontend typecheck and tests pass (npm run build, npm test)

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

