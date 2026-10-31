"""Pure, byte-preserving pin planning for a managed source/workflow pair."""

from __future__ import annotations

import re
import shlex
from packaging.version import Version, InvalidVersion

from agentic_project_kit.workspace_init import MANAGED_CI_HEADER
from agentic_project_kit.kit_ci_pin_patterns import EXACT_KIT_PIN_BYTES as _EXACT_PIN




def plan_ci_pins(
    source: bytes, workflow: bytes, version: str, *, target_template: str | None = None,
) -> dict[str, bytes]:
    from agentic_project_kit.workspace_init import CI_TEMPLATE_PATH, CI_INJECTION_TARGET

    try:
        parsed = Version(version)
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:\.post[0-9]+)?", version) or parsed.is_prerelease or str(parsed) != version:
            raise InvalidVersion(version)
    except InvalidVersion as exc:
        raise ValueError("stable_version_required") from exc
    headers = [MANAGED_CI_HEADER.encode() + ending for ending in (b"\n", b"\r\n")]
    header = next((header for header in headers if workflow == header + source), None)
    if header is None:
        raise ValueError(
            "managed_ci_pair_mismatch: workflow must equal its managed header plus source"
        )
    # Several jobs may install the Kit (KIT-GF-071: a separate classify job beside the gate job).
    # Every occurrence must be the same stable exact pin, alone on an executable pip install line.
    pins = _EXACT_PIN.findall(source)
    lines = [line for line in source.splitlines() if b"agentic-project-kit" in line]
    if not pins or source.count(b"agentic-project-kit") != len(pins) or len(set(pins)) != 1:
        raise ValueError(
            "ambiguous_ci_pin: require stable, exact Kit version pins that all name one version"
        )
    current_pin = (b"agentic-project-kit==" + pins[0]).decode("ascii")
    for line in lines:
        if line.count(b"agentic-project-kit") != 1:
            raise ValueError("ambiguous_ci_pin: require one Kit pin per install line")
        # Pin must be in an executable pip install line, not a comment or prose.
        match = re.fullmatch(rb"\s*-\s*run:\s*python(?:3)?\s+-m\s+pip\s+install\s+(.+)", line)
        if not match:
            raise ValueError("unsupported_ci_pin: require a python -m pip install run step")
        arguments = shlex.split(match[1].decode("utf-8"), comments=True)
        if current_pin not in arguments or any(
            any(operator in argument for operator in (";", "|", "&", "`", "$", ">", "<"))
            for argument in arguments
        ):
            raise ValueError(
                "unsupported_ci_pin: require a literal pip requirement without shell operators"
            )
    desired = _EXACT_PIN.sub(b"agentic-project-kit==" + version.encode("ascii"), source)
    if target_template is not None:
        # The target runtime recognized the old template's normalized hash. Its
        # replacement is part of the signed desired-file hashes, never inferred
        # from the controller's (possibly older) version.
        candidate = target_template.encode("utf-8")
        if _EXACT_PIN.findall(candidate) != [version.encode("ascii")]:
            raise ValueError("invalid_target_template_pin")
        desired = candidate
    return {CI_TEMPLATE_PATH: desired, CI_INJECTION_TARGET: header + desired}
