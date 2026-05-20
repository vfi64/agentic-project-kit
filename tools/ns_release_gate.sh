#!/usr/bin/env sh
set -eu

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  printf "%s\n" "ERROR: usage: ./ns release-gate <version>"
  printf "%s\n" "### RESULT: FAIL ###"
  exit 2
fi

PY="${PYTHON:-.venv/bin/python}"
PYTHONPATH=src "$PY" -m agentic_project_kit.release_gate_core "$VERSION"
