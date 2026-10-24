# Clauditor operations

## Scope and current state

The implemented runtime is an isolated qualification slice: authenticated OTLP
logs, traces and metrics reach a typed archive and ClickHouse, and a read-only
CLI decodes an archive record. The full appliance, live Anthropic onboarding,
Grafana dashboards, alerting, exports, production retention and restore acceptance
remain planned. Construction is paused; these instructions do not activate it.

BCF 2.3.6 Standard contract 3.0 governs this checkout. See
[environment setup](BOOTSTRAP.md), the [active ledger](../plans/phase-ledger.yml)
and [qualification review](../audits/standard-v3-readiness.yml).

## Local validation

Run from the repository root using the separate environments described in setup:

```bash
BCF_TOOL=.artifacts/bcf-tool # non-authoritative local tool environment
"$BCF_TOOL/bin/bcf" validate --repo-root .
"$BCF_TOOL/bin/bcf" exposure-scan --repo-root .
"$BCF_TOOL/bin/bcf" reconcile --repo-root . --python .venv/bin/python --check
"$BCF_TOOL/bin/bcf" ci graph validate --repo-root .
"$BCF_TOOL/bin/bcf" ci graph audit --repo-root .
.venv/bin/python spec/clauditor/v1/tools/check.py --self-test
.venv/bin/python spec/clauditor/v1/construction/tools/check.py --self-test
.venv/bin/python scripts/check_build_plan.py --self-test
.venv/bin/python -m pytest -q
.venv/bin/python tools/qualification/quality.py lint
.venv/bin/python tools/qualification/quality.py typecheck
```

The qualified baseline collected 40 tests. Test manifests and gate contracts own
exact populations; this count is a baseline observation, not a fixed test target.
Local process success is a diagnostic. Accepted BCF receipts also bind source,
commands, artifacts, controls, dependencies, interpreter and evidence session.

## Isolated Docker smoke

With Docker and Compose available:

```bash
PYTHONPATH=backend/src:tools:. .venv/bin/python tools/qualification/runtime.py
```

The probe creates a unique Compose project and ephemeral credentials, sends
synthetic signals, rejects invalid authentication and malformed JSON, checks
ClickHouse row counts and archive protobuf fidelity, then restarts the Collector
to check archive persistence. It removes its project containers, networks and
volumes on exit. It uses a container helper on the project network, so the Docker
daemon can be outside the development container. Never globally prune a shared
Docker host to clean up a failed probe.

The local `.artifacts/runtime-smoke.json` report is non-authoritative until
captured and retained by BCF. `deploy/compose.yml`, `deploy/collector.Dockerfile`
and `config/otel/qualification.yml` own the digest-pinned runtime configuration.
Collector 0.148.0 and ClickHouse 26.3 are the qualified baseline versions.
This is synthetic integration evidence, not proof of live source completeness or
365-day capacity. Do not use the qualification Compose file as a production deployment.

## Inspect an archive record

Provide one OTLP JSON export record on standard input and choose its signal:

```bash
PYTHONPATH=backend/src .venv/bin/python -m clauditor.archive.infrastructure.inspect_cli logs < /path/to/record.json
```

Use `traces` or `metrics` for the other signals. The CLI emits decoded protobuf
bytes as hexadecimal. Its input limit is 4 MiB; malformed records, unsupported
fields and empty envelopes fail validation. OTLP trace/span IDs, nested AnyValue,
large integers and binary values are covered by the archive tests. Inspection
reads input only; it does not index, persist or authenticate source provenance.

## Security checks and limits

`tools/qualification/quality.py` accepts `security-secret-scan`,
`security-dependency-audit`, `security-sbom` and `security-vulnerability-scan`.
The gates respectively scan owned source/configuration, audit the pinned Python
runtime dependencies, generate a dependency SBOM with pinned image identities,
and scan product Python source with Bandit. Full container OS-package SBOM and
vulnerability qualification remain release work. See [Security](../SECURITY.md).

## CI and evidence

[Draft PR #3](https://github.com/mjgolaszewski/clauditor/pull/3) carries the
qualification branch. [Run 40041068072](https://github.com/mjgolaszewski/clauditor/actions/runs/40041068072)
passed for head `7bd1239a2dfe94637d9a923c4b5197a558dfebe0` before this editorial
refresh. GitHub evaluated a PR merge commit whose tree matched that head exactly.
The run identifies that baseline; later edits require their own checks.

The generated workflow runs cheap preflight, project Ruff lint, four evidence
shards and terminal governance truth. Twenty gate contracts are registered;
four claims are satisfied during preflight and sixteen gates produce qualified
receipts. Receipt-producing gates run positives and typed causal negative controls
in pristine worktrees. Terminal truth checks one immutable session and exact run
attempt. A queued job or uploaded bundle alone does not establish a passing result.

`governance/ci-graph.yml` and its registered digest-locked extension own CI.
Use canonical `bcf reconcile --apply` to update generated workflows and other
derived files, then check reconciliation and graph audit. Do not edit workflow
YAML directly. Make targets are developer aliases; `make release-check` exercises
the registered gates but grants no release approval. Optional CI authority
certification remains deferred. No persistent controller or release is installed.

For local PR context, use the verifier's `bcf ci local-pr --repo-root . --python
.venv/bin/python`; it resolves the real origin comparison base. Consult the pinned
CLI's `--help` when requesting evidence capture or scoped truth. Never combine
receipts from different candidates or sessions, fabricate lifecycle truth, or
interpret product telemetry as regulatory compliance evidence.

## Maintenance and coordination

Keep execution notes in the active phase log and reports under `audits/`.
Ignored `.artifacts/` paths are non-authoritative local storage; retain referenced
proof with hashes and provider artifact identity. Cleanup is dry-run first;
follow [Repo cleanup](../governance/REPO_CLEANUP.md) and preserve reachable evidence.
Every PR updates [CHANGELOG.md](../CHANGELOG.md).

AgentBus is optional workspace coordination, separate from product runtime and
BCF authority. The Clauditor conversation enrolled successfully, acknowledged its
policy and posted its introduction after a fresh approval request. Prior HTTP 403
observations are historical. Use the installed AgentBus skill and this chat's
identity; preserve staged requests on uncertain failures, check controls, and
never copy another chat's credentials. No service token belongs in this repository.
