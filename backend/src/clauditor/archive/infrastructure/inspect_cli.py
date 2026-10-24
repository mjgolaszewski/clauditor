"""Composition root for the archive inspection CLI."""
from clauditor.archive.infrastructure.otlp_json import OTLPJSONDecoder
from clauditor.archive.routers.cli import main as route
from clauditor.archive.use_cases.queries.inspect_archive import inspect_archive


def render(signal: str, record: bytes) -> str:
    return inspect_archive(signal, record, OTLPJSONDecoder()).protobuf.hex()


def main() -> None:
    route(render)


PUBLIC_OPERATIONS = {'inspect-archive': main}

if __name__ == '__main__':
    main()
