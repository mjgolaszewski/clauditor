"""Real quality/security tool entrypoints for the declared qualification slice."""
from __future__ import annotations

import json
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OWNED = ['backend/src', 'tools/qualification', 'backend/tests/test_archive.py', 'backend/tests/test_contracts.py', 'backend/tests/test_architecture.py', 'scripts/check_build_plan.py']


def main() -> None:
    gate = sys.argv[1]
    if gate == 'lint':
        argv = [sys.executable, '-m', 'ruff', 'check', *OWNED]
    elif gate == 'typecheck':
        argv = [sys.executable, '-m', 'mypy', 'backend/src', 'tools/qualification', '--explicit-package-bases']
    elif gate == 'security-dependency-audit':
        argv = [sys.executable, '-m', 'pip_audit', '-r', 'requirements-runtime.txt', '--progress-spinner', 'off']
    elif gate == 'security-vulnerability-scan':
        argv = [sys.executable, '-m', 'bandit', '-r', 'backend/src', '-f', 'json',
                '-o', '.artifacts/vulnerability-scan.json']
    elif gate == 'security-sbom':
        for line in (ROOT / 'requirements-runtime.txt').read_text().splitlines():
            name, expected = line.split('==')
            if version(name) != expected:
                raise SystemExit('SBOM dependency inventory mismatch')
        argv = [sys.executable, '-m', 'cyclonedx_py', 'requirements', 'requirements-runtime.txt',
                '--output-file', '.artifacts/sbom.json', '--output-reproducible']
    elif gate == 'security-secret-scan':
        # detect-secrets performs real credential-pattern and entropy analysis on owned sources.
        argv = [sys.executable, '-m', 'detect_secrets', 'scan', '--all-files', *OWNED, 'config', 'deploy']
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=120, check=False)
        if result.returncode:
            raise SystemExit(result.returncode)
        report = json.loads(result.stdout)
        path = ROOT / '.artifacts/secret-scan.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + '\n')
        if report['results']:
            # Report file names, not matched credential text.
            print('credential candidates: ' + ', '.join(report['results']), file=sys.stderr)
            raise SystemExit(1)
        print('No credential candidates in owned sources/configuration')
        return
    else:
        raise SystemExit('unknown gate')
    output_dir = ROOT / '.artifacts'
    output_dir.mkdir(exist_ok=True)
    result = subprocess.run(argv, cwd=ROOT, timeout=300, check=False, text=True)
    if gate == 'security-vulnerability-scan' and result.returncode:
        report = json.loads((ROOT / '.artifacts/vulnerability-scan.json').read_text())
        print('source vulnerability findings: ' + ', '.join(r['test_id'] for r in report['results']), file=sys.stderr)
    if gate == 'security-sbom' and result.returncode == 0:
        output = ROOT / '.artifacts/sbom.json'
        report = json.loads(output.read_text())
        compose = yaml.safe_load((ROOT / 'deploy/compose.yml').read_text())
        images = {row['image'] for row in compose['services'].values() if 'image' in row}
        dockerfile = (ROOT / 'deploy/collector.Dockerfile').read_text().splitlines()[0]
        images.add(dockerfile.removeprefix('FROM '))
        for image in sorted(images):
            name, digest = image.split('@sha256:')
            report['components'].append({'type': 'container', 'name': name, 'version': 'sha256:' + digest,
                                         'hashes': [{'alg': 'SHA-256', 'content': digest}]})
        output.write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(result.returncode)


PUBLIC_OPERATIONS = {'quality': main}

if __name__ == '__main__':
    main()
