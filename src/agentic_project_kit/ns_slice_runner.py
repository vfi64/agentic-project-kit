"""Backward-compatible import shim for the neutral entrypoint slice runner.

The supported implementation lives in
:mod:`agentic_project_kit.entrypoint_slice_runner`.

This shim remains temporarily to keep historical imports stable while active
runtime paths move away from the ns-named module.
"""

from __future__ import annotations

from agentic_project_kit.entrypoint_slice_runner import *  # noqa: F403
from agentic_project_kit.entrypoint_slice_runner import main

if __name__ == "__main__":
    raise SystemExit(main())
