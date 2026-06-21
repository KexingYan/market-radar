# Architecture

Phase 1 implemented architecture:

```text
iOS SwiftUI App
        ↓
FastAPI Backend
        ↓
Provider Abstraction
        ↓
Mock Provider
```

The iOS prototype uses local Mock data and does not connect to the backend in Phase 1. The backend reads local Mock JSON files and exposes typed API routes.

## Backend

- FastAPI application.
- Pydantic domain models.
- Provider abstraction in `services/api/app/providers/base.py`.
- Mock provider in `services/api/app/providers/mock.py`.
- No database, Redis, broker, news, AI, or network dependency at runtime.

## iOS

- Native SwiftUI.
- Static local Mock data.
- Dashboard, Watchlist, Events, Reports, and Settings tabs.
- No third-party packages.
- No Apple signing or APNs configuration.

## Future Architecture, Not Implemented

The following are architectural candidates only and are not implemented:

- Futu OpenD read-only provider.
- iFinD read-only provider.
- Official filings provider.
- Licensed news provider.
- PostgreSQL persistence.
- Redis caching and rate limiting.
- AI summarization service.
- APNs notification pipeline.

Any real provider must go through the Provider abstraction, legal authorization review, credential isolation, rate limits, and data retention policy.

## Phase 3A Provider Layer

Implemented source architecture:

```text
FastAPI Routes
        ↓
Provider Registry
        ↓
Fallback Provider
        ↓
Mock Provider / SEC EDGAR Provider / Moomoo Quote Provider
```

Defaults remain `mock`. SEC EDGAR is tested with mocked HTTP transport. Moomoo quotes are tested with fake SDK adapters and no OpenD connection.

## Phase 4B Storage Layer

Implemented source architecture:

```text
API Routes
        ↓
Application Services
        ↓
Repository Protocols
        ↓
SQLite Repositories
        ↓
PROJECT_ROOT/.runtime/data/market-radar.db
```

Providers and report engines do not write SQL directly. PostgreSQL remains a future replacement option behind the repository protocols.

## Phase 4C Alert Layer

Implemented source architecture:

```text
FastAPI Alert Routes
        -> AlertService
        -> AlertEngine
        -> Repository Protocols
        -> SQLite Repositories
```

`AlertEngine` is deterministic and has no database, provider, network, notification, AI, or trading side effects. `AlertService` performs manual evaluation, checks persisted cooldown history, and saves local in-app alert records.

Phase 4C does not include APNs, system notifications, email, SMS, webhooks, background polling, schedulers, workers, live data requests, or trading.

## Phase 5A Job Orchestration

Implemented source architecture:

```text
FastAPI Job Routes / Foreground Scheduler
        -> JobService
        -> JobExecutor
        -> Static Job Registry
        -> Existing Provider, Archive, Report, and Alert Services
        -> SQLite Repositories
```

The scheduler is foreground-only and disabled by default. FastAPI startup does not begin polling. `python -m app.scheduler_runner` is the explicit foreground entry point.

No Windows service, scheduled task, startup item, hidden background worker, network listener, system notification, live provider request, AI call, or trading action is implemented.
