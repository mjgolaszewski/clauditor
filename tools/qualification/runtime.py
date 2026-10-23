"""Bounded, isolated real Collector/ClickHouse smoke; always clean up its own stack."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import cast
from urllib.error import HTTPError, URLError

from clauditor.archive.domain.envelope import Signal
from clauditor.archive.infrastructure.otlp_json import decode_json

from qualification.fixtures import signal_fixture

ROOT = Path(__file__).resolve().parents[2]


def run_smoke() -> dict:
    project = 'clauditor-qa-' + uuid.uuid4().hex[:10]
    env = dict(os.environ, CLAUDITOR_INGEST_TOKEN=secrets.token_urlsafe(32),
               CLAUDITOR_SQL_PASSWORD=secrets.token_urlsafe(32))
    base = ['docker', 'compose', '-p', project, '-f', 'deploy/compose.yml']

    def compose(*args: str) -> str:
        result = subprocess.run([*base, *args], cwd=ROOT, env=env, capture_output=True,
                                text=True, timeout=180, check=False)
        if result.returncode:
            # Do not echo credential-bearing command arguments or interpolated config.
            raise RuntimeError('Compose failed: ' + args[0] + '\n' + result.stderr[-3000:])
        return result.stdout.strip()

    helper = json.loads(compose('config', '--format', 'json'))['services']['archive-init']['image']

    def remote_http(url: str, data: bytes, headers: dict[str, str]) -> tuple[int, str]:
        # Execute on the isolated Compose network: the Docker daemon may be outside this devcontainer.
        code = """import base64,json,sys,urllib.request,urllib.error
p=json.load(sys.stdin)
r=urllib.request.Request(p['url'],data=base64.b64decode(p['data']),headers=p['headers'])
try:
 with urllib.request.urlopen(r,timeout=8) as response:
  print(json.dumps([response.status,response.read().decode()]))
except urllib.error.HTTPError as error:
 print(json.dumps([error.code,error.read().decode()]))
"""
        request = json.dumps({'url': url, 'data': base64.b64encode(data).decode(), 'headers': headers})
        result = subprocess.run(['docker', 'run', '--rm', '-i', '--network', project + '_default',
                                 '--read-only', '--cap-drop=ALL', helper, 'python', '-c', code],
                                input=request, capture_output=True, text=True, timeout=20, check=False)
        if result.returncode:
            raise RuntimeError('HTTP probe unavailable')
        status, body = json.loads(result.stdout)
        return int(status), str(body).strip()

    def post(url: str, payload: bytes, content_type: str, token: str) -> int:
        return remote_http(url, payload, {'Content-Type': content_type,
                                         'Authorization': 'Bearer ' + token})[0]

    def sql(url: str, query: str) -> str:
        auth = base64.b64encode(('ingest:' + env['CLAUDITOR_SQL_PASSWORD']).encode()).decode()
        status, body = remote_http(url, query.encode(), {'Authorization': 'Basic ' + auth})
        if status != 200:
            raise RuntimeError('SQL probe failed: ' + str(status))
        return body

    def wait_for(probe, description: str):
        deadline = time.monotonic() + 90
        last = ''
        while time.monotonic() < deadline:
            try:
                result = probe()
                if result:
                    return result
            except (HTTPError, URLError, TimeoutError, ConnectionError, RuntimeError) as error:
                last = type(error).__name__
            time.sleep(1)
        raise RuntimeError(description + ' did not become ready: ' + last)

    try:
        compose('up', '-d', '--build')
        http = 'http://collector:4318'
        database = 'http://clickhouse:8123'
        wait_for(lambda: sql(database, 'SELECT 1') == '1', 'ClickHouse')
        wait_for(lambda: post(http + '/v1/logs', b'{}', 'application/json',
                              env['CLAUDITOR_INGEST_TOKEN']) == 200, 'Collector')
        assert post(http + '/v1/logs', b'{}', 'application/json', 'invalid') in (401, 403)
        assert post(http + '/v1/logs', b'not-json', 'application/json',
                    env['CLAUDITOR_INGEST_TOKEN']) == 400
        sent = {}
        for signal in ('logs', 'traces', 'metrics'):
            fixture = signal_fixture(signal)
            payload = decode_json(cast(Signal, signal), json.dumps(fixture).encode()).protobuf
            status = post(http + '/v1/' + signal, payload, 'application/x-protobuf',
                          env['CLAUDITOR_INGEST_TOKEN'])
            assert status == 200, signal + ' ingest status ' + str(status)
            sent[signal] = payload
        counts = {}
        for table in ('otel_logs', 'otel_traces', 'otel_metrics_gauge', 'otel_metrics_histogram'):
            counts[table] = wait_for(lambda table=table: int(sql(database,
                'SELECT count() FROM clauditor.' + table)) or None, table)
        archive = {}
        # Read only this test's named volume. The helper image is digest locked in Compose.
        def archive_records(signal: str):
            code = "from pathlib import Path; print(Path('/data/archive/" + signal + ".jsonl').read_text())"
            result = subprocess.run(['docker', 'run', '--rm', '--network=none', '--read-only',
                '--mount', 'type=volume,source=' + project + '_archive,target=/data,readonly',
                helper, 'python', '-c', code], capture_output=True, text=True, timeout=30, check=False)
            if result.returncode:
                return None
            records = [decode_json(cast(Signal, signal), line.encode()).protobuf
                       for line in result.stdout.splitlines() if line.strip()]
            if records and sent[signal] not in records:
                raise ValueError('Typed archive no longer matches supplied protobuf: ' + signal)
            return records if sent[signal] in records else None
        for signal, payload in sent.items():
            records = wait_for(lambda signal=signal: archive_records(signal), signal + ' typed archive')
            archive[signal] = hashlib.sha256(payload).hexdigest()
            assert payload in records
        # Persistence check: restarting the Collector must not truncate existing archive bytes.
        compose('restart', 'collector')
        for signal in sent:
            assert wait_for(lambda signal=signal: archive_records(signal), signal + ' archive after restart')
        integer = sql(database, "SELECT LogAttributes['typed.integer'] FROM clauditor.otel_logs LIMIT 1")
        assert integer == '9007199254740993'
        return {'scope': 'synthetic local OTLP; no live Anthropic coverage or release claim',
                'signals': list(sent), 'indexed_counts': counts, 'protobuf_sha256': archive,
                'unauthorized_rejected': True, 'malformed_rejected': True,
                'archive_restart_preserved': True, 'status': 'pass'}
    finally:
        if sys.exc_info()[0] is not None:
            logs = compose('logs', '--tail=30')
            for secret in (env['CLAUDITOR_INGEST_TOKEN'], env['CLAUDITOR_SQL_PASSWORD']):
                logs = logs.replace(secret, '[redacted]')
            print(logs[-6000:], file=sys.stderr)
        compose('down', '--volumes', '--remove-orphans')


def main() -> None:
    report = run_smoke()
    output = ROOT / '.artifacts/runtime-smoke.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, sort_keys=True))


PUBLIC_OPERATIONS = {'runtime-smoke': main}

if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    main()
