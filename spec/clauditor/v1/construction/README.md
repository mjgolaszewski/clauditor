# Clauditor — candidate dependency-first construction plan

**Planning only; no implementation, authenticated BCF evidence, release approval or Standard-v3 promotion.**
The source is the exact Anthropic OTLP requirements candidate at `44ca22d86ea15b6c9e76d84217cbabf37bd5cda9`.

## Authoritative candidate records

- `plan.json`: all requirements, proposed P02–P09 stages, 45 work-order summaries, resource-compatible dependency waves and source coverage.
- `orders/CL-WO-NNN.json`: individually bounded, context-source-linked A–J implementation/verification packets.
- `index.json`: complete packet inventory; workers read **one** relevant packet plus `context.json` and required predecessor outputs, not one massive work-order document.
- `schema/*.schema.json`: Draft 2020-12 shape validation; `tools/check.py` handles relational closure.
- `context.json`: fixed BCF/source pointers; no duplicate BCF ontology or acceptance authority.

## Verify and generate readable projections

From a qualified repository Python environment with `jsonschema`:

```bash
python3 spec/clauditor/v1/construction/tools/check.py --self-test
python3 spec/clauditor/v1/construction/tools/check.py --render-order CL-WO-027 --emit-dir /tmp/clauditor-plan
```

The generated Markdown and digest manifest belong outside the repository; do not commit massive generated artifacts.

## End-to-end demonstrations

1. `CL-WO-027`: Cowork/Claude Code prompt, tool and available response → OTel Collector → typed archive → ClickHouse → authenticated reviewer session view.
2. `CL-WO-041`: multi-source compliance dashboard, alert, evidence export, source-gap indicators and restore.
3. `CL-WO-045`: operator-ready Docker appliance with measured retention and separately qualified BCF/governance release handoff.

## Preservation and acceptance

Existing `main`, the correctly uploaded `assets/clauditor-hero.png`, all BCF Lite files and the current P01 phase are untouched.
P02–P09 are **proposed stage labels only**; root `plans/build-plan.yml` and `plans/phase-ledger.yml` remain operative and cannot be overwritten or advanced by this document.
All 45 packets are `not_admitted`. A BCF evaluator and authorized owner must qualify exact dependencies, current schemas, evidence and actual execution scope.

Known blockers: source plan/version/content eligibility; API inbound host TLS/DNS on port 443; ClickHouse alpha metrics export qualification; Grafana OSS detailed audit limits; actual disk sizing for 365/90/31 days; owner approval.
Absent provider data, tool outputs or file bytes cannot be fabricated, and a valid hash does not establish semantic or SEC-recordkeeping completeness.
