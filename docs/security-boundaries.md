# Security Boundaries

## File System Boundary

Agents may operate only inside the current repository. They must not access parent directories, user home directories, desktops, downloads, cloud drives, unrelated projects, or paths reached through links outside this repository.

## Credential Boundary

Agents must not read, search, display, copy, or modify real secrets, including `.env`, API tokens, SSH keys, Apple certificates, broker credentials, database passwords, browser cookies, or account data.

## Network Boundary

Phase 1 must not make external network requests. No dependency installation, scraping, uploads, live API tests, broker connections, or public server exposure.

## API Boundary

Only Mock Provider APIs are allowed in Phase 1. Real quote, news, filing, AI, broker, and account APIs are out of scope.

## Trading Boundary

No order placement, cancellation, simulated trading, holdings, balances, account history, trade passwords, rebalancing, signals, target prices, or leverage suggestions.

## Logging Boundary

Logs must not include tokens, passwords, account identifiers, authorization headers, provider secrets, or broker account data.

## Mobile Boundary

The mobile app must not store broker passwords, real provider credentials, Apple signing assets, provisioning profiles, or APNs credentials. It must not directly connect to broker desktop gateways.

## Codex Operation Boundary

Codex must not delete files, overwrite existing files, run destructive Git commands, execute sudo, install global packages, access the network, or operate outside the repository without explicit approval and a revised safety scope.
