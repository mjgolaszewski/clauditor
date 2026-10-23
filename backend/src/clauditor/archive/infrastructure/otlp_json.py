"""Decode the qualified Collector OTLP JSON file representation with official types."""
import base64
import json
from typing import Any

from clauditor.archive.domain.envelope import ArchiveEnvelope, Signal, envelope
from google.protobuf.json_format import ParseDict
from google.protobuf.message import Message
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

MAX_RECORD_BYTES = 4 * 1024 * 1024
SIGNALS: dict[str, type[Message]] = {
    'logs': ExportLogsServiceRequest,
    'metrics': ExportMetricsServiceRequest,
    'traces': ExportTraceServiceRequest,
}


def decode_json(signal: Signal, record: bytes) -> ArchiveEnvelope:
    """Reject malformed/unknown fields; preserve OTLP numeric and AnyValue types."""
    if len(record) > MAX_RECORD_BYTES:
        raise ValueError('archive record exceeds limit')
    if signal not in SIGNALS:
        raise ValueError('unsupported signal')
    value: Any = json.loads(record)
    if not isinstance(value, dict) or not value:
        raise ValueError('expected nonempty OTLP object')
    normalize_ids(signal, value)
    message = ParseDict(value, SIGNALS[signal](), ignore_unknown_fields=False)
    return envelope(signal, message.SerializeToString(deterministic=True))


class OTLPJSONDecoder:
    """Official-protobuf adapter for the archive decoder port."""

    def decode(self, signal: str, record: bytes) -> ArchiveEnvelope:
        from typing import cast
        return decode_json(cast(Signal, signal), record)


def normalize_ids(signal: Signal, value: dict[str, Any]) -> None:
    """OTLP JSON uses hex IDs, unlike the protobuf JSON parser's base64 bytes."""
    resource_key, scope_key, record_key = (
        ('resourceSpans', 'scopeSpans', 'spans') if signal == 'traces'
        else ('resourceLogs', 'scopeLogs', 'logRecords')
    )
    if signal == 'metrics':
        return
    for resource in value.get(resource_key, []):
        for scope in resource.get(scope_key, []):
            for record in scope.get(record_key, []):
                for item in [record, *record.get('links', [])]:
                    for key, size in [('traceId', 16), ('spanId', 8), ('parentSpanId', 8)]:
                        if item.get(key):
                            raw = bytes.fromhex(item[key])
                            if len(raw) != size:
                                raise ValueError('invalid OTLP identifier length')
                            item[key] = base64.b64encode(raw).decode()
