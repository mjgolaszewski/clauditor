# Clauditor bootstrap — canonical BCF Lite first

Clauditor is a public, ordinary BCF adopter; no persistent controller is
required. The current seed targets BCF Lite, then Standard profile contract 3.0
only after complete real product gates and semantic authority are available.

## Canonical runtime pin

- Source: https://github.com/mjgolaszewski/bcf-governance
- Immutable release: v2.3.6
- Asset: bcf_governance-2.3.6-py3-none-any.whl
- SHA-256: `1ee73f7f8ba69803917ee72c0625907621d6c9b582d11d88346fd9cd5dcd5ab7`
- Reference upstream main at review: `e39d72a0b0e2e849317e284a674848bbb7fcf000`

## Initial installation

The repository's initial bootstrap workflow invokes
`scripts/bootstrap-lite.sh` on a clean, committed `main`. That script
downloads the immutable BCF wheel, independently checks its exact digest,
installs the canonical BCF pack in a local ignored virtual environment,
runs strict Lite validation and exposure scan, and commits only the
canonical generated outputs. The initial bootstrap passed canonical strict Lite validation, but the GitHub Actions token could not itself introduce the generated governance workflow. The generated workflow bytes were therefore staged and admitted through the authenticated repository connection, which then removed the one-time bootstrap workflow. No persistent bootstrap writer remains.

The workflow is not itself proof that the install succeeded. Check the
latest `main` contents for `governance-profile.yml` with
`profile.selected: lite`, `AGENTS.yml`, installed scripts, plans,
and the GitHub Actions outcome.

For a clean local checkout with a supported Python 3.11–3.14,
`git`, `curl` and network access, run:

```bash
bash scripts/bootstrap-lite.sh
.venv/bin/bcf validate --repo-root .
.venv/bin/bcf exposure-scan --repo-root .
.venv/bin/bcf doctor --repo-root .
```

The script refuses a dirty tree or an existing governance profile. Never
use a local handmade BCF surrogate. Review and commit changes before
pushing a locally executed bootstrap.

## Standard v3 (applied to the bounded qualification slice)

Complete gate argv/inputs/negative controls, semantic families, application
operations and canonical representations against real product code. Then:

```bash
bcf semantic-ownership scaffold --repo-root . --output /tmp/clauditor-semantics.yml
bcf profile promote --repo-root . --to standard --contract-version 3.0 \
  --config /path/to/complete-standard-gates.yml \
  --semantic-config /path/to/approved-semantics.yml --check
# Review and authorize the exact promotion first.
bcf profile promote --repo-root . --to standard --contract-version 3.0 \
  --config /path/to/complete-standard-gates.yml \
  --semantic-config /path/to/approved-semantics.yml --apply
bcf reconcile --repo-root . --check
bcf ci graph validate --repo-root .
bcf ci graph audit --repo-root . --format json
```

No fake/no-op gates, invented classifications, controller Apps, self-governance
overlays, or authored verified/closed claims.

The local BCF verifier and project interpreter have separate environment custody.
The project dependencies are pinned in `requirements-governance.txt`; the canonical
installer requires pip 26.2.2. Use the authenticated BCF 2.3.6 wheel for the verifier.
Current promotion and qualification observations are recorded in
`audits/standard-v3-readiness.yml` and `phases/phase-01-log.yml`.
