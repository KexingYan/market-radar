# Phase 5C Moomoo Runtime Isolation

Phase 5C isolates Moomoo SDK runtime files before any lazy SDK import.

## Runtime Layout

Runtime location type:

```text
project_runtime/.runtime/moomoo/
```

Declared subdirectories:

- `logs/`
- `cache/`
- `tmp/`

These paths are inside `PROJECT_ROOT` and are ignored by Git through the existing runtime ignore rule.

## Behavior

- Runtime isolation runs before importing the Moomoo SDK.
- SDK runtime settings are applied only to the current process.
- System PATH, shell profiles, registry, user configuration, and OpenD configuration are not modified.
- If runtime isolation fails, the Moomoo provider returns `sdk_runtime_isolation_failed`.
- If SDK logging setup is blocked during import, the provider returns `sdk_logging_blocked`.
- Both failure modes fall back to Mock data through the provider fallback layer.

## What Phase 5C Did Not Do

Phase 5C did not:

- connect to OpenD
- open a Quote Context
- connect to `127.0.0.1:11111`
- request real quotes
- request SEC
- read Moomoo account data
- query holdings or assets
- query orders or trades
- output real prices
- write SDK logs to a user directory
- add telemetry
- trade

Before any future live validation, the user must manually start and log in to OpenD. Live validation remains a separate user-approved step.
