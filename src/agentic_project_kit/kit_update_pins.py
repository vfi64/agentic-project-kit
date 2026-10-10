"""Pure, byte-preserving pin planning for a managed source/workflow pair."""

from __future__ import annotations

import re
import shlex

from agentic_project_kit.workspace_init import MANAGED_CI_HEADER


_EXACT_PIN = re.compile(rb"agentic-project-kit==([0-9]+\.[0-9]+\.[0-9]+)(?![\w.+!*-])")


def plan_ci_pins(source: bytes, workflow: bytes, version: str) -> dict[str, bytes]:
    from agentic_project_kit.workspace_init import CI_TEMPLATE_PATH, CI_INJECTION_TARGET

    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("stable_version_required")
    headers = [MANAGED_CI_HEADER.encode() + ending for ending in (b"\n", b"\r\n")]
    header = next((header for header in headers if workflow == header + source), None)
    if header is None:
        raise ValueError(
            "managed_ci_pair_mismatch: workflow must equal its managed header plus source"
        )
    if source.count(b"agentic-project-kit") != 1 or len(_EXACT_PIN.findall(source)) != 1:
        raise ValueError("ambiguous_ci_pin: require exactly one stable, exact Kit version pin")
    # Pin must be in an executable pip install line, not a comment or prose.
    line = next(line for line in source.splitlines() if b"agentic-project-kit" in line)
    match = re.fullmatch(rb"\s*-\s*run:\s*python(?:3)?\s+-m\s+pip\s+install\s+(.+)", line)
    if not match:
        raise ValueError("unsupported_ci_pin: require a python -m pip install run step")
    arguments = shlex.split(match[1].decode("utf-8"), comments=True)
    current_pin = b"agentic-project-kit==" + _EXACT_PIN.findall(source)[0]
    if current_pin.decode("ascii") not in arguments or any(
        any(operator in argument for operator in (";", "|", "&", "`", "$", ">", "<"))
        for argument in arguments
    ):
        raise ValueError(
            "unsupported_ci_pin: require a literal pip requirement without shell operators"
        )
    desired = _EXACT_PIN.sub(b"agentic-project-kit==" + version.encode("ascii"), source)
    return {CI_TEMPLATE_PATH: desired, CI_INJECTION_TARGET: header + desired}
