# AGENTS.md

Long-term operating rules for agents working in this repository:

1. Only modify the current repository.
2. Do not access files outside the repository.
3. Do not read `.env` or any real secrets.
4. Do not delete existing files.
5. Do not run destructive Git commands.
6. Do not run `sudo`.
7. Do not perform global installs.
8. Do not access the network without explicit user approval.
9. Do not connect to real market data APIs without explicit user approval.
10. Do not implement trading or order placement without explicit user approval.
11. All real data providers must be integrated through the Provider abstraction layer.
12. Mobile clients must not store broker passwords.
13. Mobile clients must not directly connect to broker desktop gateways.
14. All new APIs must have type definitions and tests.
15. All Mock data must be clearly marked.
16. All user-visible market data must display a timestamp and whether it is delayed.
17. AI-generated content must be stored separately from source facts.
18. AI content must not impersonate original news.
19. Do not log tokens, passwords, or account information.
20. Any operation that may overwrite files must stop and report.
21. Dependencies may only be installed into `PROJECT_ROOT/.venv`.
22. The backend may only bind to `127.0.0.1` for local development.
23. Tests must not access the public internet.
24. The iOS app may only connect to the local Mock API.
25. Do not automatically replace `localhost` or `127.0.0.1` with a LAN address.
26. Do not add broad ATS exceptions such as arbitrary HTTP loads.
27. Do not add telemetry, analytics, crash upload, or advertising SDKs.
28. Do not create background resident processes.
29. Do not start Phase 3B without explicit user approval.
30. Project-local uv must live under `.tools/uv`.
31. uv-managed Python must live under `.runtime/python`.
32. uv cache must live under `.cache/uv`.
33. Do not modify system PATH or shell profiles for Python or uv.
34. Alert evaluation is manual in Phase 4C; do not add background polling, schedulers, workers, or resident alert processes.
35. Alerts are local in-app database records only; do not send APNs, system notifications, email, SMS, webhooks, or chat messages.
36. Alert rules must be deterministic, typed, and validated; do not add eval, exec, dynamic expressions, scripts, or user-provided code execution.
37. Alerts must not contain investment advice, target prices, buy/sell instructions, account data, positions, assets, credentials, or trading actions.
38. Do not add physical delete or bulk clear endpoints for alerts or alert rules without explicit user approval and a retention design.
34. Phase 3A tests must not connect to OpenD or probe port 11111.
35. SEC EDGAR tests must use mocked transports unless live validation is explicitly approved.
36. Moomoo quote code must remain read-only and must not import or call trading APIs.
37. Provider fallback must preserve safe failure reasons without returning stack traces.
38. Do not infer, discover, or write a user's email address for SEC configuration.
39. Phase 4A report generation must remain deterministic, offline, and free of investment advice.
40. Report engines must not call AI, live data providers, databases, or trading APIs.
41. Phase 4B SQLite files must stay under `.runtime/data` or `.runtime/test-data`.
42. Do not allow clients to submit database paths.
43. Do not add destructive storage APIs such as full-table delete, drop, truncate, or automatic cleanup.
44. Watchlist APIs must stay local-only and must not sync broker watchlists.
45. Phase 5A scheduler must remain foreground-only and disabled by default.
46. Do not register Windows services, scheduled tasks, startup items, or resident background workers.
47. Job handlers must come from a static whitelist and must not execute shell commands or dynamic user-provided functions.
48. Job run summaries must store aggregate counts only, not full payloads, paths, credentials, accounts, holdings, or stack traces.
