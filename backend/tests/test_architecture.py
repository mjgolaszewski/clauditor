"""Enforce actual custom-code and native-service boundaries of the current slice."""
import ast
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCES = list((ROOT / 'backend/src').rglob('*.py'))
GATES = ['architecture-module-size', 'architecture-layer-membership', 'architecture-context-membership',
         'architecture-import-boundaries', 'architecture-cqrs-side', 'architecture-router-thinness',
         'architecture-duplication', 'architecture-test']


@pytest.mark.parametrize('gate', GATES)
def test_boundary(gate):
    rules = yaml.safe_load((ROOT / 'architecture-boundaries.yml').read_text())['architecture']
    assert SOURCES, 'cannot qualify architecture with no source'
    cfg = yaml.safe_load((ROOT / 'config/otel/qualification.yml').read_text())
    for path in SOURCES:
        source = path.read_text()
        tree = ast.parse(source)
        if gate in ('architecture-module-size', 'architecture-test'):
            assert len(source.splitlines()) <= rules['production_module_policy']['max_loc']
        if gate in ('architecture-layer-membership', 'architecture-test'):
            assert sum(layer in path.parts for layer in ['domain', 'infrastructure', 'ports', 'use_cases', 'routers']) == 1
        if gate in ('architecture-context-membership', 'architecture-test'):
            assert path.relative_to(ROOT / 'backend/src/clauditor').parts[0] == 'archive'
        if gate in ('architecture-import-boundaries', 'architecture-test') and 'domain' in path.parts:
            imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
            assert all(not name.startswith(('google', 'opentelemetry', 'clauditor.archive.infrastructure'))
                       for name in imports)
        if gate in ('architecture-cqrs-side', 'architecture-test'):
            writes = {'write_text', 'write_bytes', 'commit', 'unlink', 'execute'}
            assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                           and node.func.attr in writes for node in ast.walk(tree))
    if gate in ('architecture-router-thinness', 'architecture-test'):
        # Native ingress delegates decoding/authentication to qualified OSS components.
        assert set(cfg['receivers']) == {'otlp'}
        assert set(cfg['receivers']['otlp']['protocols']) == {'http'}
        assert cfg['receivers']['otlp']['protocols']['http']['auth']['authenticator'] == 'bearertokenauth'
        assert set(cfg['processors']) == {'batch'}
    if gate in ('architecture-duplication', 'architecture-test'):
        functions = []
        for path in SOURCES:
            functions += [ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(path.read_text()))
                          if isinstance(n, ast.FunctionDef)]
        assert len(functions) == len(set(functions))
