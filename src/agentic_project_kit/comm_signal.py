from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CONTRACT_PATH = "docs/governance/CHAT_COMMUNICATION_CONTRACT.md"
VALID_SIGNALS = {"d", "f", "w"}


@dataclass(frozen=True)
class CommSignalInspection:
    signal: str
    status: str
    next_action: str
    contract_path: str = CONTRACT_PATH
    evidence_path: Path | None = None
    evidence_found: bool = False

    @property
    def success(self) -> bool:
        return self.status == "PASS"


def inspect_comm_signal(signal: str, *, evidence_path: Path | None = None) -> CommSignalInspection:
    normalized = signal.strip().lower()
    evidence_found = bool(evidence_path and evidence_path.exists())
    if normalized not in VALID_SIGNALS:
        return CommSignalInspection(
            signal=signal,
            status="FAIL",
            next_action="unknown communication signal; inspect the communication contract before continuing",
            evidence_path=evidence_path,
            evidence_found=evidence_found,
        )
    if normalized == "d":
        return CommSignalInspection(
            signal=normalized,
            status="PASS" if evidence_found else "FAIL",
            next_action=(
                "inspect evidence before continuing; d is not evidence"
                if evidence_found
                else "do not treat d as success until repo or remote evidence is available"
            ),
            evidence_path=evidence_path,
            evidence_found=evidence_found,
        )
    if normalized == "f":
        return CommSignalInspection(
            signal=normalized,
            status="PASS" if evidence_found else "FAIL",
            next_action=(
                "diagnose existing evidence before asking for pasted output"
                if evidence_found
                else "look for remote or repo evidence before requesting pasted output"
            ),
            evidence_path=evidence_path,
            evidence_found=evidence_found,
        )
    return CommSignalInspection(
        signal=normalized,
        status="PASS" if evidence_found else "FAIL",
        next_action=(
            "continue only after confirming evidence and current repo state"
            if evidence_found
            else "verify repo state before continuing; w is not evidence"
        ),
        evidence_path=evidence_path,
        evidence_found=evidence_found,
    )


def render_comm_signal_inspection(inspection: CommSignalInspection) -> str:
    lines = [
        "COMM_SIGNAL_INSPECTION",
        f"signal: {inspection.signal}",
        f"status: {inspection.status}",
        f"contract: {inspection.contract_path}",
        f"evidence_found: {'yes' if inspection.evidence_found else 'no'}",
        f"next_action: {inspection.next_action}",
    ]
    if inspection.evidence_path is not None:
        lines.append(f"evidence_path: {inspection.evidence_path}")
    lines.append(f"### RESULT: {'PASS' if inspection.success else 'FAIL'} ###")
    return "\n".join(lines)
