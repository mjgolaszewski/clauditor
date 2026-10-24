# Clauditor — candidate dependency-first construction plan

**Candidate construction packets; execution state belongs to the canonical YAML ledgers.**
Standard-v3 promotion and a bounded synthetic qualification slice are complete.
These packets do not themselves confer implementation acceptance, BCF admission
or release approval.
The source baseline is the Anthropic OTLP requirements candidate at `44ca22d86ea15b6c9e76d84217cbabf37bd5cda9`.
The reviewed retry-contract amendment and refreshed exact model blob are recorded
in `audits/standard-v3-readiness.yml`; `plan.json` and packets bind the amended blob.

## Authoritative candidate records

- `plan.json`: all requirements, proposed P02–P09 stages, 45 work-order summaries, resource-compatible dependency waves and source coverage.
- `orders/CL-WO-NNN.json`: individually bounded, context-source-linked A–J implementation/verification packets.
- `index.json`: complete packet inventory; workers read **one** relevant packet plus `context.json` and required predecessor outputs, not one massive work-order document.
- `schema/*.schema.json`: Draft 2020-12 shape validation; `tools/check.py` handles relational closure.
- `context.json`: fixed BCF/source pointers; no duplicate BCF ontology or acceptance authority.

## Verify and generate readable projections

From a qualified repository Python environment with `jsonschema`:

```bash
.venv/bin/python spec/clauditor/v1/construction/tools/check.py --self-test
.venv/bin/python spec/clauditor/v1/construction/tools/check.py --render-order CL-WO-027 --emit-dir /tmp/clauditor-plan
```

The generated Markdown and digest manifest belong outside the repository; do not commit massive generated artifacts.

## End-to-end demonstrations

1. `CL-WO-027`: Cowork/Claude Code prompt, tool and available response → OTel Collector → typed archive → ClickHouse → authenticated reviewer session view.
2. `CL-WO-041`: multi-source compliance dashboard, alert, evidence export, source-gap indicators and restore.
3. `CL-WO-045`: operator-ready Docker appliance with measured retention and separately qualified BCF/governance release handoff.

## Preservation and acceptance

The owner-uploaded `assets/clauditor-hero.png` is preserved. BCF 2.3.6 now runs
Standard profile contract 3.0; the historical Lite baseline remains provenance.
The root YAML roadmap and planned P02–P09 phase artifacts now adopt this delivery
sequence. Root `plans/build-plan.yml` and `plans/phase-ledger.yml` own execution;
these candidate packets cannot activate phases or confer admission.
The owner authorized the minimum construction needed for promotion eligibility.
P01 qualified the actual OTLP/archive/SQL slice, promoted Standard 3.0, verified
provider CI and pushed the branch. P01 is now paused; full MVP work is pending.
All 45 packets are `not_admitted`. A BCF evaluator and authorized owner must qualify exact dependencies, current schemas, evidence and actual execution scope.
Runtime reports use ignored `.artifacts/clauditor/` destinations with exact digest
references retained in phase logs; test sources never serve as runtime receipts.

Remaining qualification work includes source plan/version/content eligibility,
API inbound host TLS/DNS on port 443, live metric shapes beyond the synthetic
gauge/histogram probe, Grafana OSS detailed audit limits, measured disk sizing
for 365/90/31 days and approval of subsequent construction scope.
Absent provider data, tool outputs or file bytes cannot be fabricated, and a valid hash does not establish semantic or SEC-recordkeeping completeness.
