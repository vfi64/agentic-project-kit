#!/usr/bin/env python3
"""Temporary remote command slot.

This file is intentionally inert. Use `.venv/bin/agentic-kit remote-next`
as the canonical dialog and GUI execution path.
"""

from __future__ import annotations


def main() -> int:
    print("NEXT_REMOTE_COMMAND is deprecated. Use: .venv/bin/agentic-kit remote-next")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
