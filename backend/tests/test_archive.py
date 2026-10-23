import json

import pytest
from clauditor.archive.domain.envelope import envelope
from clauditor.archive.infrastructure.otlp_json import SIGNALS, decode_json
from google.protobuf.json_format import MessageToDict, ParseDict, ParseError

from qualification.fixtures import signal_fixture


@pytest.mark.parametrize('signal', ['logs', 'traces', 'metrics'])
def test_typed_roundtrip(signal):
    source = signal_fixture(signal)
    decoded = decode_json(signal, json.dumps(source).encode())
    message = SIGNALS[signal]()
    message.ParseFromString(decoded.protobuf)
    if signal == 'traces':
        span = source['resourceSpans'][0]['scopeSpans'][0]['spans'][0]
        import base64
        span['traceId'] = base64.b64encode(bytes.fromhex(span['traceId'])).decode()
        span['spanId'] = base64.b64encode(bytes.fromhex(span['spanId'])).decode()
    expected = ParseDict(source, SIGNALS[signal]())
    assert MessageToDict(message) == MessageToDict(expected)
    assert decoded.signal == signal


def test_nested_anyvalue_precision():
    value = decode_json('logs', json.dumps(signal_fixture('logs')).encode())
    message = SIGNALS['logs']()
    message.ParseFromString(value.protobuf)
    attrs = message.resource_logs[0].scope_logs[0].log_records[0].attributes
    assert attrs[0].value.int_value == 9007199254740993
    assert attrs[1].value.bytes_value == b'\x00\x01\xff'
    assert attrs[2].value.array_value.values[0].bool_value is True


@pytest.mark.parametrize('value', [b'{}', b'[]', b'not JSON', b'{"unknown":true}'])
def test_malformed_archive_rejected(value):
    with pytest.raises((ValueError, ParseError)):
        decode_json('logs', value)


def test_envelope_rejects_empty_bytes():
    with pytest.raises(ValueError, match='empty'):
        envelope('logs', b'')


def test_size_limit():
    with pytest.raises(ValueError, match='limit'):
        decode_json('logs', b' ' * (4 * 1024 * 1024 + 1))
