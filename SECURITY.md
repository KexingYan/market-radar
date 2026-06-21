# Security Policy

## Reporting Security Issues

Report security concerns privately to the repository owner. Do not publish credentials, exploit details, or sensitive account information in public issues.

## Credential Rules

- Credentials must never be committed.
- Do not store real API keys, broker credentials, Apple certificates, provisioning profiles, database passwords, or cloud secrets in this repository.
- `.env.example` may contain only fake placeholders.

## If a Secret Is Found

1. Stop work on the affected area.
2. Do not copy or display the secret.
3. Notify the repository owner.
4. Rotate the credential outside this repository.
5. Remove the secret through a deliberate history-cleaning process chosen by the owner.

## Local Services

Local services must not expose public network interfaces by default. Development servers should bind to local-only addresses unless explicitly reviewed.

Phase 2 backend development must bind only to `127.0.0.1`. Do not use `0.0.0.0`, LAN addresses, public tunnels, or cloud hosts for the Mock API.

Phase 2 Python tooling must remain project-local: uv in `.tools/uv`, managed Python in `.runtime/python`, cache in `.cache/uv`, and the virtual environment in `.venv`. Do not modify system PATH or install global Python packages.

## Providers

Real providers must use least privilege, read-only access by default, documented authorization, and clear data retention rules.

Phase 3A adds source code for free-data providers only. SEC EDGAR validation is offline by default. Moomoo quote validation is offline by default and uses fake adapters; OpenD is not installed, started, probed, or logged in during Phase 3A.

SEC live validation is deferred until the user can safely configure `SEC_USER_AGENT`. Do not infer, discover, or write a user email address into repository files.

Phase 4A reports are deterministic and offline. They must not call AI, live SEC, OpenD, paid data sources, databases, or trading APIs.

Phase 4B local SQLite storage must stay inside project runtime storage. The API must not expose absolute database paths, connection strings, file permissions, user names, or environment variables. Watchlist persistence is local-only and must not store holdings, costs, balances, orders, or broker account data.

Phase 4C alerts are local in-app database records only. They must not send APNs, system notifications, email, SMS, webhooks, or chat messages. Alert evaluation is manual and must not start background workers, polling loops, schedulers, Windows services, or resident processes.

Alert rules must be deterministic and strongly validated. Do not add arbitrary expressions, `eval`, `exec`, user scripts, dynamic imports, trading actions, buy/sell recommendations, target prices, account reads, holdings reads, or asset reads.

Phase 5A job orchestration is local and foreground-only. The scheduler must remain disabled by default and must not register Windows services, scheduled tasks, startup items, resident workers, public listeners, or LAN listeners. Job handlers must come from a static whitelist and must not execute shell commands or dynamic user-selected functions.

Job run records must store safe aggregate summaries only. They must not store full market payloads, full report text, tracebacks, paths, credentials, tokens, email addresses, account identifiers, holdings, assets, orders, or trade history.

Phase 5C isolates Moomoo SDK runtime files before any lazy SDK import. Moomoo SDK logs, cache, and temporary files must stay under project runtime storage. If the SDK attempts user-directory logging or runtime isolation fails, the provider must fall back to Mock data and must not open a Quote Context, connect to OpenD, request quotes, read accounts, query holdings, query assets, or expose stack traces.

## Trading

This project does not implement trading, order placement, account balance reads, holdings reads, or broker account login.

## Logging

Logs must redact tokens, passwords, account identifiers, API keys, and authorization headers.

## Mobile Credentials

The mobile app must not store broker passwords or long-lived provider secrets. Real provider credentials, if ever added, must be handled by the backend with minimal scope.

## Data Source Compliance

Only authorized data sources may be used. Provider terms must be checked before storing, displaying, forwarding, summarizing, or deriving analytics from licensed data.
