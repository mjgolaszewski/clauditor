#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
BCF_VERSION=2.3.6
BCF_WHEEL="bcf_governance-${BCF_VERSION}-py3-none-any.whl"
BCF_SHA256=1ee73f7f8ba69803917ee72c0625907621d6c9b582d11d88346fd9cd5dcd5ab7
BCF_URL="https://github.com/mjgolaszewski/bcf-governance/releases/download/v${BCF_VERSION}/${BCF_WHEEL}"

for cmd in git curl python3; do
  command -v "$cmd" >/dev/null || { echo "Missing $cmd" >&2; exit 2; }
done
test -d .git || { echo "Git repository required" >&2; exit 2; }
test "$(git rev-parse --show-toplevel)" = "$ROOT" || { echo "Wrong Git root" >&2; exit 2; }
git rev-parse --verify HEAD >/dev/null
if [ -f governance-profile.yml ]; then
  echo "BCF governance is already installed; refusing to resynthesize" >&2
  exit 2
fi
test -z "$(git status --porcelain)" || { echo "BCF requires a clean committed HEAD" >&2; exit 2; }

python3 -m venv .venv
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
curl -fLSs --retry 3 --connect-timeout 20 "$BCF_URL" -o "$tmpdir/$BCF_WHEEL"
".venv/bin/python" - "$tmpdir/$BCF_WHEEL" "$BCF_SHA256" <<'PY_HASH'
from pathlib import Path
import hashlib, sys
digest=hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()
if digest != sys.argv[2]:
    raise SystemExit(f"BCF wheel SHA-256 mismatch: {digest}")
print(f"BCF wheel SHA-256 authenticated: {digest}")
PY_HASH
".venv/bin/python" -m pip install "$tmpdir/$BCF_WHEEL"
".venv/bin/bcf" install \
  --target "$ROOT" \
  --profile lite \
  --project-id clauditor \
  --project-name "Clauditor" \
  --product-name "Clauditor" \
  --date "$(date -u +%F)" \
  --require-strict-validation
".venv/bin/bcf" validate --repo-root .
".venv/bin/bcf" exposure-scan --repo-root .
git add -A
git commit -m "chore: install canonical BCF Lite v2.3.6"
echo "Canonical Lite pack installed and validated at $(git rev-parse --short HEAD)"
