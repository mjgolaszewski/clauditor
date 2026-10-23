"""Read-only archive inspection delegates representation semantics to its decoder."""
from clauditor.archive.domain.envelope import ArchiveEnvelope
from clauditor.archive.ports.decoder import ArchiveDecoder


def inspect_archive(signal: str, record: bytes, decoder: ArchiveDecoder) -> ArchiveEnvelope:
    return decoder.decode(signal, record)
