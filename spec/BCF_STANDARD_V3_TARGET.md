# BCF Standard-v3 target: ordinary adopter, no persistent controller

**Status:** Standard profile contract 3.0 promoted and provider-verified for the bounded qualification slice; construction is paused. This is not full product acceptance or release certification.

**Canonical source:** [BCF Governance](https://github.com/mjgolaszewski/bcf-governance), verified at upstream `main` commit `e39d72a0b0e2e849317e284a674848bbb7fcf000` on 2026-10-23. **Pin for bootstrap:** immutable `v2.3.6` release and its wheel digest recorded in `docs/BOOTSTRAP.md`. No repo-local reinterpretation of BCF schemas, lifecycle states, or provider authority is authorized.

## 1. Adoption decisions

| Decision | Target / boundary |
| --- | --- |
| Initial install | Canonical `bcf install --profile lite --require-strict-validation` after a clean initial Git commit |
| Upgrade path | `bcf profile promote --to standard --contract-version 3.0`, after `--check` review, then `--apply` |
| Controller | **No installed or long-lived trusted controller**; ordinary adopter, not BCF self-governance |
| Control execution | Canonical executable BCF verifier and ephemeral trusted GitHub Actions lanes when required; no project-specific controller daemon |
| CI owner | `governance/ci-graph.yml`, rendered deterministically by BCF after promotion |
| Human authority | Intent, risk acceptance, protected-branch/release decisions, material exceptions |
| Release claims | Fail closed until relevant exact-subject evidence and provider authority are authenticated |
| Runtime source | Immutable release-bound BCF wheel; no invented local governance engine |
| Product design | Deferred to next scope; do not invent executable gates or claim product semantics before they exist |

The canonical graph may describe its executable control mechanism using a `trusted_controller` field. Its schema is BCF-owned: **do not delete or rewrite that field merely because the project does not deploy a persistent controller**. The prohibition applies to controller management infrastructure and self-governance machinery, not to all trusted CI execution.

## 2. Dependency-outward construction order

1. **Invariant.** Name an actual product obligation, failure mode, and forbidden state before specifying an implementation.
2. **Canonical domain owner.** Declare a unique owner for each semantic family; use BCF's single-owner invariant principle (SOIP), not a parallel owner registry.
3. **Primitive / operation.** Enumerate public operations, command/query separation, effects, sources, sinks, trust boundaries, and identity/tenant exposure.
4. **Contracts and state machines.** Close each reachable transition and producer–consumer edge with typed acceptance, rejection, recovery, and explicit exclusions for impossible edges.
5. **Producers and consumers.** Map adapters, runtime events, OTLP spans/metrics/logs, storage/exports, and dependent components to their canonical ownership and exact interfaces.
6. **Evidence.** Provide executable positive tests, typed negative controls, manifest-bound test populations, exact source dependencies, and appropriate review/authority for consequential claims.
7. **Delivery.** Translate accepted contracts into bounded build units and CI lanes; update the canonical BCF ledgers without authoring computed lifecycle truth.

This chain constrains the *later* product specification; it is not itself evidence that Clauditor satisfies the chain.

## 3. Standard-v3 promotion prerequisites

All of the following must be satisfied before promotion—not approximated with `echo`, no-ops, version-only probes, or all-skipped tests:

- Real **architecture**, **lint**, **typecheck**, **unit/integration test**, and **contract** gates with explicit `argv`, environment, outputs, timeout policy, and typed causal negative controls.
- Real **security** gates as applicable: secret detection, dependency vulnerability assessment, SBOM, source/container scanning, and runtime-smoke evidence. Profile-mandatory gates must be executable, not merely declared.
- The independent semantic-family, application-operation, canonical representation, and provenance inventory, all resolved against real source symbols or typed BCF-supported exclusions.
- A complete `--profile-config` / `--semantic-config` accepted by the canonical installer/promoter, with project-specific gates added through the BCF `gates` and `gate_catalog` contract.
- Explicit candidate and trusted-runner **resource mappings**. Prefer appropriate ephemeral GitHub-hosted runners if the canonical graph and trust contract permit them. No hosted polling, idle-wait, or long-lived controller runner.
- `governance/ci-graph.yml` compiled and reconciled by the current BCF release. Project CI changes must use registered digest-locked extensions; do not hand-edit generated workflow YAML.
- Pull-request preflight before costly work, required gate ownership, immutable session / exact run-attempt fan-in, and terminal `bcf truth` with scoped evidence reuse only when dependency fingerprints and authority allow it.
- An explicit decision and review before changing GitHub branch protection or adoption policy. Repository creation and code push do not confer release approval.

The exact mandatory gate set, command parameters, and trust boundaries must follow the live canonical v3 release, not this summary when they differ. Required yet unavailable gates block promotion.

## 4. Controller exclusion (in scope, out of scope)

**Exclude:** controller build/installation/rotation state; installed trusted-controller management; BCF self-governance overlays; BCF-specific publication, recovery, or repository-control Apps/credentials; trusted-controller recovery lanes and controller custody claims.

**Retain:** ordinary BCF preflight, evidence, truth, canonical CI graph, trusted transient control jobs when required, protected-branch authority, human review/merge, exact-run/attempt provenance, and supported GitHub provider validation. A controller-free topology is not a trust-free topology.

## 5. Evidence and claims

- Authoring `completed` is not permission to author `verified` or `closed`; those are computed from accepted evidence.
- Never mark Lite bootstrap as Standard-v3 validation or imply a green scaffolding check proves the future product.
- Distinguish the **observability signals** that Clauditor may eventually collect from the **governance evidence** BCF uses to accept software delivery claims.
- Provider-only facts must be authenticated from the relevant provider boundary, not reconstructed from model-generated text.
- Freshness invalidation and authenticated reuse are mandatory. Uncertain evidence is not quietly promoted to truth.

## 6. Acceptance checkpoints

The next agent/developer task should complete and record these in BCF's *installed* governance artifacts, not in a second shadow lifecycle file:

- [x] The seed was committed at a clean Git HEAD.
- [x] Canonical BCF v2.3.6 wheel digest was authenticated and Lite was installed with strict validation.
- [x] `bcf validate` and `bcf exposure-scan` passed during canonical Lite installation; initial Lite artifacts and the generated workflow were committed.
- [x] The GitHub repository is confirmed **public** and contains the hero and this README.
- [ ] Product invariants, operations, and source/sink scope are approved.
- [x] Standard-v3 gate and actual-source semantic configs are complete and accepted by the canonical promotion checker (not an independent release review).
- [x] `bcf profile promote ... --check` passed and the matching `--apply` succeeded.
- [x] `bcf reconcile --repo-root . --check` and `bcf ci graph validate/audit` pass after any canonical apply/reconciliation.
- [x] No persistent controller or self-governance overlay was introduced.
- [ ] Provider-backed CI adoption and protection, if chosen, are explicitly reviewed; no fabricated `verified`, `closed`, or release claims.

**Current stop point:** Standard 3.0 was promoted and provider-verified; construction is paused by owner request. The qualification branch is pushed. Full MVP construction and release require subsequent work.
