import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_otlp_receivers_require_authentication():
    cfg = yaml.safe_load((ROOT / 'config/otel/qualification.yml').read_text())
    assert cfg['receivers']['otlp']['protocols']['http']['auth']['authenticator'] == 'bearertokenauth'
    assert cfg['extensions']['bearertokenauth']['token'] == '${env:CLAUDITOR_INGEST_TOKEN}'
    for signal in ['logs', 'metrics', 'traces']:
        assert cfg['service']['pipelines'][signal]['exporters'] == [f'file/{signal}', 'clickhouse']
        assert cfg['exporters'][f'file/{signal}']['append'] is True


def test_retry_does_not_assert_archive_success():
    model = json.loads((ROOT / 'spec/clauditor/v1/model.json').read_text())
    ingest = next(m for m in model['state_machines'] if m['id'] == 'cl.machine.ingest.v1')
    retry = next(t for t in ingest['transitions'] if t['event'] == 'retry')
    assert retry['to'] == 'accepted'
    archived = [t for t in ingest['transitions'] if t['to'] == 'archived']
    assert all(t['event'] == 'archive_ok' for t in archived)


def test_canonical_plan_positive_and_negative_controls():
    from scripts.check_build_plan import load_inputs, self_test, validate
    data = load_inputs(ROOT)
    assert validate(data)['requirements'] == 39
    assert len(self_test(data)) >= 5


def test_collector_accepts_the_actual_configuration():
    image = 'otel/opentelemetry-collector-contrib@sha256:8164eab2e6bca9c9b0837a8d2f118a6618489008a839db7f9d6510e66be3923c'
    # Build context works with both local and remote Docker daemons; no host-path assumptions.
    subprocess.run(['docker', 'build', '-q', '-f', 'deploy/collector.Dockerfile', '-t',
                    'clauditor-collector-contract', '.'], cwd=ROOT, check=True, capture_output=True)
    result = subprocess.run(['docker', 'run', '--rm', '-e', 'CLAUDITOR_INGEST_TOKEN=synthetic-test-token',  # pragma: allowlist secret
                             '-e', 'CLAUDITOR_SQL_PASSWORD=synthetic-test-password',  # pragma: allowlist secret
                             'clauditor-collector-contract', 'validate', '--config=/etc/otelcol-contrib/config.yaml'],
                            cwd=ROOT, capture_output=True, text=True, check=False)
    assert '@sha256:' in image
    assert result.returncode == 0, result.stderr


def test_runtime_evidence_destinations():
    plan = json.loads((ROOT / 'spec/clauditor/v1/construction/plan.json').read_text())
    for order in plan['work_orders']:
        output = order['primary_output']
        assert not output.startswith('tests/') or output.startswith('tests/fixtures/')
