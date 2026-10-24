# Security policy

Clauditor has an implemented synthetic qualification slice and no released
production service. Standard-v3 checks qualify the declared development scope;
they do not establish regulatory compliance, live provider completeness or
production security acceptance.

## Reporting

Keep secrets, raw model conversations, API keys, private logs and sensitive
telemetry out of public issues and proof-of-concept attachments. Use GitHub
private vulnerability reporting if enabled; otherwise contact the repository
owner through an established private channel. A formal reporting channel and
supported-version policy remain prerequisites for product release.

## Current security coverage

The registered gates scan owned code and configuration for credential candidates,
audit pinned Python runtime dependencies, run Bandit against product source and
generate a dependency SBOM with pinned container identities. Runtime probes use
synthetic data and ephemeral credentials and test authentication rejection and
malformed input. Full container OS-package inventories and vulnerability scans,
production TLS/access control, live data handling and appliance hardening remain
future acceptance obligations. See the [operations runbook](docs/OPERATIONS.md)
for exact scope and the [candidate specification](spec/clauditor/v1/README.md)
for product requirements.

Do not commit credentials, local AgentBus profiles or tokens, unredacted telemetry,
or private evidence. Keep local environments and probe outputs in ignored paths.
