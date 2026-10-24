# Clauditor — machine-readable product specification (v1 candidate)

This is an invariant-first, BCF-mapped **candidate product contract**, not
a claim that the full product is implemented or admitted. Standard profile
contract 3.0 is installed and provider-verified for a separate bounded
qualification slice; this candidate does not confer that authority.

The authoritative input set consists of:

- `model.json`: doctrine, unique domain owners, invariants/laws/primitives,
  explicit operations and machines, independent producer-consumer obligations,
  contracted routes, typed exclusions, acceptance obligations, and known gaps.
- `source-registry.json`: owner decisions, official published references,
  independently retained mandatory source and state-transition obligations.
- `schema/*.schema.json`: Draft 2020-12 structural validation.
- `bcf-binding.json`: candidate mapping authored against the historical Lite
  baseline and Standard-v3 target. Its candidate status and Lite field do not
  override the installed Standard profile in root `governance-profile.yml`.
- `tools/check.py`: structural and relational validator; deterministic
  generated human report, pair/state matrices and diagram; causal mutations.

The canonical YAML roadmap now maps all requirements to planned phase workitems.
This adopts delivery intent, not product implementation or BCF semantic admission.
The reviewed retry amendment requires a new `archive_ok` observation after retry;
its provenance and promotion history are in
`audits/standard-v3-readiness.yml`.

## Validate without writing

Use the Python 3.12 project environment from [setup](../../../docs/BOOTSTRAP.md):

```bash
.venv/bin/python spec/clauditor/v1/tools/check.py --self-test
```

To generate a human-readable specification and matrices **outside this source
directory**, use:

```bash
.venv/bin/python spec/clauditor/v1/tools/check.py --self-test \
  --emit-dir /tmp/clauditor-spec-derived
```

The generated Markdown, CSV, DOT graph and manifest are never independent
semantic authority. Generated output should not be hand-edited or checked
in as a competing copy. A passing local validation is not an authenticated
BCF EvidenceReceipt.

## Required sequence

1. Review owner intent, sources, limitations and the incomplete external
   qualification observations documented in `model.json`.
2. Validate canonical element references and schema.
3. Derive state-event and producer-consumer pair closure, rejecting missing
   independently required contracts and unrecognized typed exclusions.
4. Run cause-specific negative mutations and confirm expected failure codes.
5. Qualify OpenTelemetry/Anthropic fixtures and component versions with real
   integration probes **before** declaring construction tasks admissible.
6. Reconcile approved product semantics with `plans/product-spec.yml` and
   canonical BCF semantic/operation owners non-destructively. Do not replace
   entire root registries, forge receipts or change rendered workflow YAML.
7. Read the generated bounded construction packets and canonical phase records.
   The roadmap and Standard-v3 promotion are adopted; full MVP construction
   remains paused. Resume only within a subsequent owner-authorized task.

### Important source limitations

Cowork OTLP is not a guarantee of full web/cloud session text or artifact
bytes. Claude Code content requires explicit flags and can truncate/omit
tool results, especially binary and background outputs. Anthropic API traces
are at least-once/best-effort, may be missing, and require a public HTTPS
destination on port 443. This product records these conditions as coverage
and provenance constraints; it cannot recover bytes the provider never sent.

The design favors free, self-hosted OTel Collector + ClickHouse + Grafana OSS
and a typed OTLP archive. Components with alpha/beta exporter maturity
must be qualified against fixture formats and observed source data.
