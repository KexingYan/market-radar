# Moomoo OpenD Manual Setup

Phase 3A does not install, start, configure, probe, or log in to OpenD.

OpenD is not currently started by this project.

Live Moomoo validation is deferred to a separate user-approved Phase 3B.

## Phase 3A Status

- Read-only quote provider source exists.
- SDK adapter source exists.
- Offline fake adapter tests pass.
- No real quote context is created during tests.
- No connection attempt is made to `127.0.0.1:11111`.

## Future Phase 3B Requirements

Before live validation:

- User manually starts OpenD.
- User confirms read-only quote validation.
- The app must not ask for broker passwords.
- The app must not unlock trading.
- The app must not query accounts, holdings, balances, orders, or history.
- The app must not place or modify orders.

Phase 3B must remain read-only.

## Phase 5B Validation Status

Moomoo live validation remained read-only and did not complete a quote request.

Recorded result:

- OpenD installation: not attempted.
- OpenD startup: not attempted.
- OpenD login: not attempted.
- Quote context opened: no.
- Snapshot request sent: no.
- Real price output: no.
- Account, holdings, assets, orders, or trades queried: no.
- Context close: not applicable because no context was opened.
- Fallback Mock behavior: used.

The SDK attempted user-level logging setup before a quote context was opened. The sandbox blocked that user-directory operation, so validation stopped without accessing OpenD or requesting a quote.

## Phase 5C Runtime Isolation

Phase 5C adds project-local runtime isolation for the Moomoo SDK before any lazy SDK import.

Runtime location type:

```text
project_runtime/.runtime/moomoo/
```

Declared project-local subdirectories:

- `logs/`
- `cache/`
- `tmp/`

The app configures SDK runtime paths for the current process only. It does not modify system environment variables permanently, system PATH, shell profiles, registry, user configuration, or OpenD configuration.

Phase 5C did not:

- install OpenD
- start OpenD
- log in to OpenD
- open a Quote Context
- connect to `127.0.0.1:11111`
- request real quotes
- read accounts
- query holdings or assets
- output real prices

If SDK logging or runtime isolation is blocked, the provider returns a safe reason and falls back to Mock data.

## Phase 6A Live E2E Status

Moomoo OpenD was used for a one-shot AAPL-only read-only E2E validation.

Recorded result:

- Target: local OpenD only.
- Symbol: `US.AAPL` only.
- Quote Context opened: yes.
- Snapshot returned: yes.
- Quote Context closed: yes.
- Real price output: no.
- Account read: no.
- Holdings or assets queried: no.
- Orders or trades queried: no.
- Trading performed: no.

The live E2E endpoint returns snapshot row counts and success flags only. It does not return real prices or quote tables.

## Phase 6B Watchlist Refresh Status

Moomoo OpenD was used for a one-shot watchlist refresh validation.

Recorded result:

- Source symbols: enabled local watchlist with fixed fallback.
- Processed symbol count: 1.
- Quote Context opened: yes.
- Snapshot rows returned: 1.
- Quote Context closed: yes.
- Real price output: no.
- Account read: no.
- Holdings or assets queried: no.
- Orders or trades queried: no.
- Trading performed: no.

The watchlist refresh endpoint returns snapshot row counts and success flags only. It does not return real prices or quote tables.
