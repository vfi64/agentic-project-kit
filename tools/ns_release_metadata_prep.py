#!/usr/bin/env python3
"""Backward-compatible wrapper for release metadata preparation.

The supported implementation lives in
:mod:`agentic_project_kit.release_metadata_prep`.

This wrapper intentionally exposes `date` for historical tests and callers that
monkeypatch the legacy script module directly.
"""

from __future__ import annotations

from datetime import date

from agentic_project_kit import release_metadata_prep as _impl


def main(argv: list[str] | None = None) -> int:
    _impl.date = date
    return _impl.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
