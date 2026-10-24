"""Archive decoding boundary; providers do not confer custody or indexing authority."""
from typing import Protocol

from clauditor.archive.domain.envelope import ArchiveEnvelope


class ArchiveDecoder(Protocol):
    def decode(self, signal: str, record: bytes) -> ArchiveEnvelope: ...
