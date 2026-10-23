"""Synthetic OTLP only: these values never establish live Anthropic coverage."""
import time
from typing import Any


def signal_fixture(signal: str) -> dict[str, Any]:
    resource = {'attributes': [{'key': 'service.name', 'value': {'stringValue': 'clauditor-qualification'}}]}
    now = str(time.time_ns())
    scope: dict[str, Any]
    if signal == 'logs':
        record: dict[str, Any] = {'timeUnixNano': now, 'body': {'stringValue': 'synthetic prompt: archive qualification'},
                  'attributes': [{'key': 'typed.integer', 'value': {'intValue': '9007199254740993'}},
                                 {'key': 'typed.bytes', 'value': {'bytesValue': 'AAH/'}},
                                 {'key': 'typed.nested', 'value': {'arrayValue': {'values': [
                                     {'boolValue': True}, {'doubleValue': 1.25}]}}}]}
        scope = {'scopeLogs': [{'scope': {'name': 'clauditor.synthetic'}, 'logRecords': [record]}]}
    elif signal == 'traces':
        record = {'traceId': '0102030405060708090a0b0c0d0e0f10', 'spanId': '0102030405060708',
                  'name': 'synthetic request', 'kind': 1, 'status': {}, 'startTimeUnixNano': now,
                  'endTimeUnixNano': str(int(now) + 1000000)}
        scope = {'scopeSpans': [{'scope': {'name': 'clauditor.synthetic'}, 'spans': [record]}]}
    elif signal == 'metrics':
        point = {'timeUnixNano': now, 'asInt': '9007199254740993'}
        hist = {'timeUnixNano': now, 'count': '3', 'sum': 4.5, 'bucketCounts': ['1', '2'],
                'explicitBounds': [1.0]}
        scope = {'scopeMetrics': [{'scope': {'name': 'clauditor.synthetic'}, 'metrics': [
            {'name': 'qualification.gauge', 'gauge': {'dataPoints': [point]}},
            {'name': 'qualification.histogram', 'histogram': {'aggregationTemporality': 2,
                                                          'dataPoints': [hist]}}]}]}
    else:
        raise ValueError('unsupported signal')
    key = {'logs': 'resourceLogs', 'traces': 'resourceSpans', 'metrics': 'resourceMetrics'}[signal]
    return {key: [{'resource': resource, **scope}]}
