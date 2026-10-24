"""Thin CLI translation for inspecting one OTLP archive record."""
import argparse
import sys
from collections.abc import Callable


def main(query: Callable[[str, bytes], str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('signal', choices=['logs', 'traces', 'metrics'])
    args = parser.parse_args()
    print(query(args.signal, sys.stdin.buffer.read(4 * 1024 * 1024 + 1)))
