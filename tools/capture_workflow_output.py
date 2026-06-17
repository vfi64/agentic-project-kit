#!/usr/bin/env python3
"""Portable workflow output capture helper.

This replaces shell-only capture helpers for supported local workflow use.
It reads stdin and writes the exact stream to the requested output file while
also echoing it to stdout.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def capture(output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = sys.stdin.buffer.read()
    output_path.write_bytes(data)
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture stdin to a file and stdout.")
    parser.add_argument("output", help="Output file path")
    args = parser.parse_args(argv)
    return capture(Path(args.output))


if __name__ == "__main__":
    raise SystemExit(main())
