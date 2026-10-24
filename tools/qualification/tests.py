"""Execute exact pytest populations; JUnit is captured by the canonical BCF runtime."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    gate = sys.argv[1]
    if gate == 'test':
        selectors = ['backend/tests/test_archive.py']
    elif gate == 'contract-test':
        selectors = ['backend/tests/test_contracts.py']
    elif gate.startswith('architecture-'):
        names = {
            'architecture-module-size': ['test_production_modules_respect_loc_cap'],
            'architecture-layer-membership': ['test_production_modules_map_to_exactly_one_layer'],
            'architecture-context-membership': ['test_production_modules_map_to_exactly_one_bounded_context'],
            'architecture-import-boundaries': ['test_domain_layer_does_not_import_frameworks_clients_or_outer_layers',
                                               'test_use_cases_do_not_import_http_objects_or_infrastructure_clients',
                                               'test_ports_do_not_import_sqlalchemy_or_concrete_adapters',
                                               'test_routers_do_not_import_persistence_models_or_external_clients_directly'],
            'architecture-cqrs-side': ['test_cqrs_query_side_does_not_mutate_state',
                                       'test_cqrs_command_side_does_not_return_read_model_shapes'],
            'architecture-router-thinness': ['test_routers_remain_thin_transport_adapters'],
            'architecture-duplication': ['test_bounded_context_duplication_is_explicit',
                                          'test_shared_abstraction_duplication_has_minimum_real_call_sites'],
        }
        selectors = [f'backend/tests/architecture/test_boundaries_ast.py::{name}'
                     for name in names[gate]] if gate in names else ['backend/tests/architecture',
                                                                 'backend/tests/test_architecture.py']
    else:
        raise SystemExit('unknown test gate')
    output_dir = ROOT / '.artifacts/junit'
    output_dir.mkdir(parents=True, exist_ok=True)
    raise SystemExit(pytest.main([*selectors, '-q', '--junitxml=.artifacts/junit/' + gate + '.xml']))


PUBLIC_OPERATIONS = {'tests': main}

if __name__ == '__main__':
    main()
