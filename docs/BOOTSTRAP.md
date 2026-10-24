# Development environment and BCF adoption

Clauditor uses BCF 2.3.6 with Standard profile contract 3.0. Lite bootstrap and
Standard promotion are complete on `plan/standard-v3-readiness`; see
[draft PR #3](https://github.com/mjgolaszewski/clauditor/pull/3).
Product construction remains paused in the canonical phase ledger.

## Set up an existing checkout

Use Python 3.12, Git and network access. The runtime smoke additionally needs a
reachable Docker daemon with Compose. Keep the BCF verifier environment separate
from the project environment; do not install the BCF distribution into `.venv`.

Run from the repository root:

```bash
set -euo pipefail
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-governance.txt
BCF_TOOL=.artifacts/bcf-tool # non-authoritative local tool environment
BCF_WHEEL=$(mktemp)
curl -fL --output "$BCF_WHEEL" https://github.com/mjgolaszewski/bcf-governance/releases/download/v2.3.6/bcf_governance-2.3.6-py3-none-any.whl
printf '%s  %s\n' 1ee73f7f8ba69803917ee72c0625907621d6c9b582d11d88346fd9cd5dcd5ab7 "$BCF_WHEEL" | sha256sum -c -
mkdir -p "$(dirname "$BCF_TOOL")"
python3.12 -m venv "$BCF_TOOL"
BCF_WHEEL_DIR=$(mktemp -d)
cp "$BCF_WHEEL" "$BCF_WHEEL_DIR/bcf_governance-2.3.6-py3-none-any.whl"
"$BCF_TOOL/bin/python" -m pip install "$BCF_WHEEL_DIR/bcf_governance-2.3.6-py3-none-any.whl"
rm "$BCF_WHEEL"
rm -r "$BCF_WHEEL_DIR"
"$BCF_TOOL/bin/bcf" doctor --repo-root .
```

`requirements-governance.txt` pins the project tools, including pip 26.2.2.
`requirements-runtime.txt` declares the narrower product dependency inventory.
The immutable wheel digest above is the authenticated runtime pin used for adoption.
A doctor warning about unconfigured optional CI authority certification is recorded;
it does not mean product release certification exists.

## Validate the checkout

Follow [Operations](OPERATIONS.md). Validation reads the installed profile;
re-running Lite bootstrap on this repository is unnecessary and is rejected by
the bootstrap script when a governance profile already exists.

## Adoption history

`scripts/bootstrap-lite.sh` installed the canonical Lite pack from the same
verified wheel. The initial Actions token could not introduce the generated
workflow, so the authenticated repository connection admitted those bytes and
removed the one-time bootstrap workflow. Standard promotion later used
`governance/standard-v3-profile.yml` and `governance/standard-v3-semantics.yml`:
canonical `profile promote --check`, review of the concrete changes, matching
`--apply`, and canonical reconciliation. No persistent controller was installed.

The [promotion record](../audits/standard-v3-readiness.yml) and
[phase log](../phases/phase-01-log.yml) retain the observations. Promotion is a
completed adoption transaction, not a setup step for every developer. Future
profile or workflow changes must use canonical BCF commands and the declared
YAML owners; generated workflow files are deterministic projections.
