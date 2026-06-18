from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re


PATCH_FAILURE_PATTERNS: tuple[str, ...] = (
    "block not found",
    "expected block not found",
    "assertion block not found",
    "function not found",
    "not found or not uniquely",
    "not uniquely replaced",
    "patch failed",
    "patch guard",
    "old assertion still",
    "old log assertion still",
    "expected current",
    "anchor not found",
)

DIAGNOSIS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"RESULT=.*DIAGNOS.*DONE", re.IGNORECASE),
    re.compile(r"RESULT=.*PATCH_FAILURE.*DONE", re.IGNORECASE),
    re.compile(r"PATCH_FAILURE_DIAGNOSIS_DONE", re.IGNORECASE),
    re.compile(r"actual file state", re.IGNORECASE),
    re.compile(r"exact .*test functions", re.IGNORECASE),
    re.compile(r"exact .*diff", re.IGNORECASE),
    re.compile(r"diagnose .*file.*state", re.IGNORECASE),
)

DEFAULT_SCAN_GLOBS: tuple[str, ...] = (
    "docs/reports/command_runs/**/*.md",
    "docs/reports/command_runs/**/*.txt",
    "docs/reports/command_runs/**/*.json",
)

TMP_SCAN_GLOBS: tuple[str, ...] = (
    "tmp/*.log",
    "tmp/*.txt",
    "tmp/*.json",
)


@dataclass(frozen=True)
class PatchFailureSignal:
    path: str
    group: str
    kind: str
    detail: str
    mtime_ns: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PatchFailureDisciplineResult:
    root: str
    signals: tuple[PatchFailureSignal, ...]
    violations: tuple[PatchFailureSignal, ...]

    @property
    def ok(self) -> bool:
        return not self.violations

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "patch_failure_discipline_audit",
            "root": self.root,
            "status": self.status,
            "signal_count": len(self.signals),
            "violation_count": len(self.violations),
            "signals": [signal.as_dict() for signal in self.signals],
            "violations": [signal.as_dict() for signal in self.violations],
        }


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _group_for_path(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    name = path.name
    match = re.match(r"(slice\d+)", name)
    if match:
        return match.group(1)
    match = re.match(r"([a-z0-9]+(?:-[a-z0-9]+){0,3})-\d{8}-\d{6}", name)
    if match:
        return match.group(1)
    if relative.startswith("docs/reports/"):
        return relative.rsplit("/", 1)[0]
    return path.stem


def _discover_logs(root: Path, *, include_tmp: bool) -> tuple[Path, ...]:
    globs = list(DEFAULT_SCAN_GLOBS)
    if include_tmp:
        globs.extend(TMP_SCAN_GLOBS)
    paths: list[Path] = []
    for pattern in globs:
        for path in root.glob(pattern):
            if path.is_file() and path not in paths:
                paths.append(path)
    return tuple(sorted(paths))


def _signals_for_file(path: Path, root: Path) -> tuple[PatchFailureSignal, ...]:
    text = _safe_read(path)
    lowered = text.lower()
    group = _group_for_path(path, root)
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        mtime_ns = 0

    signals: list[PatchFailureSignal] = []
    matched = [pattern for pattern in PATCH_FAILURE_PATTERNS if pattern in lowered]
    if matched:
        signals.append(
            PatchFailureSignal(
                path=path.relative_to(root).as_posix(),
                group=group,
                kind="patch_failure",
                detail=", ".join(sorted(matched))[:500],
                mtime_ns=mtime_ns,
            )
        )

    if any(pattern.search(text) for pattern in DIAGNOSIS_PATTERNS):
        signals.append(
            PatchFailureSignal(
                path=path.relative_to(root).as_posix(),
                group=group,
                kind="diagnosis",
                detail="diagnosis marker found",
                mtime_ns=mtime_ns,
            )
        )

    return tuple(signals)


def _violations(signals: tuple[PatchFailureSignal, ...]) -> tuple[PatchFailureSignal, ...]:
    by_group: dict[str, list[PatchFailureSignal]] = {}
    for signal in signals:
        by_group.setdefault(signal.group, []).append(signal)

    violations: list[PatchFailureSignal] = []
    for group, group_signals in by_group.items():
        ordered = sorted(group_signals, key=lambda item: (item.mtime_ns, item.path, item.kind))
        failures_since_diagnosis = 0
        last_failure: PatchFailureSignal | None = None
        for signal in ordered:
            if signal.kind == "diagnosis":
                failures_since_diagnosis = 0
                last_failure = None
                continue
            if signal.kind == "patch_failure":
                failures_since_diagnosis += 1
                last_failure = signal

        if failures_since_diagnosis >= 2 and last_failure is not None:
            violations.append(
                PatchFailureSignal(
                    path=last_failure.path,
                    group=group,
                    kind="missing_diagnosis_after_repeated_patch_failure",
                    detail=(
                        "two or more patch-failure signals occurred without a later "
                        "diagnosis marker in the same group"
                    ),
                    mtime_ns=last_failure.mtime_ns,
                )
            )

    return tuple(violations)


def audit_patch_failure_discipline(
    root: Path = Path("."),
    *,
    include_tmp: bool = False,
) -> PatchFailureDisciplineResult:
    root = root.resolve()
    signals: list[PatchFailureSignal] = []
    for path in _discover_logs(root, include_tmp=include_tmp):
        signals.extend(_signals_for_file(path, root))

    signal_tuple = tuple(sorted(signals, key=lambda item: (item.group, item.mtime_ns, item.path, item.kind)))
    return PatchFailureDisciplineResult(
        root=root.as_posix(),
        signals=signal_tuple,
        violations=_violations(signal_tuple),
    )


def render_patch_failure_discipline(result: PatchFailureDisciplineResult) -> str:
    lines = [
        "PATCH_FAILURE_DISCIPLINE_AUDIT",
        f"STATUS={result.status}",
        f"SIGNAL_COUNT={len(result.signals)}",
        f"VIOLATION_COUNT={len(result.violations)}",
    ]
    for violation in result.violations:
        lines.append(f"VIOLATION={violation.group}|{violation.path}|{violation.detail}")
    for signal in result.signals:
        lines.append(f"SIGNAL={signal.kind}|{signal.group}|{signal.path}|{signal.detail}")
    return "\n".join(lines) + "\n"
