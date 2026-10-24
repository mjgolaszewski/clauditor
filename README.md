# Clauditor

<p align="center">
  <img src="assets/clauditor-hero.png" alt="Clauditor — OpenTelemetry observability and audit for Anthropic" width="960">
</p>

<p align="center"><strong>Every invocation leaves evidence.</strong></p>

**Clauditor** makes Anthropic model and tool activity inspectable through correlated traces, metrics, logs and retained source records. It is being built for compliance administrators who need to understand what happened, which source reported it and where the record is incomplete.

The product target is a single-tenant, self-hosted Linux Docker Compose appliance built around the OpenTelemetry Collector, ClickHouse OSS and Grafana OSS. Its source scope includes eligible Cowork/Claude sessions, Claude Code, Anthropic API traces and instrumented SDK traces.

## What you can inspect

- **Activity:** model requests, tool calls and service boundaries, correlated where the source supplies usable identifiers.
- **Performance:** latency, throughput, failures and token usage; cost where reliable usage and pricing inputs exist.
- **Content:** source-emitted prompts, responses, tool records and available artifacts, with explicit coverage and truncation indicators.
- **Provenance:** which source produced a record, how it was handled and what the retained evidence can support.

Coverage depends on what each source actually emits. Clauditor cannot reconstruct omitted tool output, unavailable artifact bytes or internal model processing from exterior telemetry. The [product specification](spec/clauditor/v1/README.md) defines these limits and the intended acceptance obligations.

## Available today

The repository contains a working qualification slice with:

- Authenticated OTLP ingestion of synthetic logs, traces and metrics.
- A typed archive and ClickHouse indexing.
- Tests for malformed input, authentication rejection, archive fidelity and persistence across a Collector restart.
- A read-only CLI for inspecting an OTLP archive record.

Full appliance construction is paused. Live source onboarding, Grafana dashboards, alerts, exports, production retention sizing and appliance acceptance remain planned. The hero illustrates the product vision; this repository does not yet provide a production release.

## Start here

| You want to… | Read |
| --- | --- |
| Set up a development environment | [Development setup](docs/BOOTSTRAP.md) |
| Validate the checkout, run the isolated smoke or inspect an archive | [Operations](docs/OPERATIONS.md) |
| Understand product requirements and source limitations | [Product specification](spec/clauditor/v1/README.md) |
| Explore the delivery plan | [Construction guide](spec/clauditor/v1/construction/README.md) and [canonical roadmap](plans/build-plan.yml) |
| Check execution state | [Active phase ledger](plans/phase-ledger.yml) |
| Review notable changes | [Changelog](CHANGELOG.md) |

## Governed development

<img src="https://raw.githubusercontent.com/mjgolaszewski/bcf-governance/main/docs/assets/bcf-governance-pack-hero.jpg" width="168" align="right" alt="BCF Governance">

Clauditor uses [BCF Governance](https://github.com/mjgolaszewski/bcf-governance) **2.3.6**, with **Standard profile contract 3.0**, to enforce architectural boundaries, semantic ownership, executable gates and causal negative controls. BCF computes delivery claims from source-bound evidence. The project uses ephemeral CI workers and has no persistent BCF controller.

[AGENTS.yml](AGENTS.yml) defines contributor instructions. Canonical YAML under `plans/` and `governance/` owns scope, execution state and gate contracts; generated workflows are maintained through BCF reconciliation. See the [governance guide](spec/BCF_STANDARD_V3_TARGET.md) for authority and evidence boundaries.

Development checks and product telemetry serve different purposes. Neither alone establishes regulatory compliance, completeness of provider data or correctness of model output.

<br clear="right">

## License and security

See [LICENSE](LICENSE) for usage terms and [SECURITY.md](SECURITY.md) for reporting guidance and current security coverage. Keep credentials, private conversations and sensitive telemetry out of public issues and build logs.
