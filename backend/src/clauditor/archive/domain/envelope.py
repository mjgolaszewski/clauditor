"""A decoded source envelope remains distinct from indexing or durable receipt."""
from dataclasses import dataclass
from typing import Literal

Signal = Literal['logs', 'traces', 'metrics']


@dataclass(frozen=True)
class ArchiveEnvelope:
    """Source-faithful protobuf bytes; no claim of authenticated source completeness."""

    signal: Signal
    protobuf: bytes


def envelope(signal: Signal, protobuf: bytes) -> ArchiveEnvelope:
    """Construct only decoded, nonempty signal payloads."""
    if signal not in ('logs', 'traces', 'metrics') or not protobuf:
        raise ValueError('empty or unsupported OTLP envelope')
    return ArchiveEnvelope(signal=signal, protobuf=protobuf)
