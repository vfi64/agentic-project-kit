from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal


class CompletionOutcome(str, Enum):
    PASS = "PASS"
    PASS_ALREADY_DONE = "PASS_ALREADY_DONE"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CompletionClassification:
    outcome: CompletionOutcome
    reason: str
    matched_phrase: str | None = None
    target_state: str | None = None

    @property
    def success(self) -> bool:
        return self.outcome in {CompletionOutcome.PASS, CompletionOutcome.PASS_ALREADY_DONE}


TargetState = Literal["git-clean", "remote-sync", "pull-request-exists", "branch-exists"]

SUPPORTED_TARGET_STATES: frozenset[str] = frozenset({
    "git-clean",
    "remote-sync",
    "pull-request-exists",
    "branch-exists",
})

DEFAULT_TARGET_STATES: frozenset[str] = frozenset({
    "git-clean",
    "remote-sync",
    "pull-request-exists",
})


@dataclass(frozen=True)
class NoOpSuccessPattern:
    phrase: str
    reason: str
    target_states: frozenset[str]


NO_OP_SUCCESS_PATTERNS: tuple[NoOpSuccessPattern, ...] = (
    NoOpSuccessPattern("nothing to commit, working tree clean", "git commit target state already clean", frozenset({"git-clean"})),
    NoOpSuccessPattern("nothing to commit", "git commit target state already clean", frozenset({"git-clean"})),
    NoOpSuccessPattern("working tree clean", "worktree already clean", frozenset({"git-clean"})),
    NoOpSuccessPattern("no changes to commit", "no changes to commit", frozenset({"git-clean"})),
    NoOpSuccessPattern("everything up-to-date", "remote already up to date", frozenset({"remote-sync"})),
    NoOpSuccessPattern("already up to date", "local branch already up to date", frozenset({"remote-sync"})),
    NoOpSuccessPattern("a pull request for branch", "pull request already exists", frozenset({"pull-request-exists"})),
    NoOpSuccessPattern("pull request already exists", "pull request already exists", frozenset({"pull-request-exists"})),
    NoOpSuccessPattern("a branch named", "branch already exists", frozenset({"branch-exists"})),
)

HARD_FAIL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("traceback", "python traceback"),
    ("syntaxerror", "python syntax error"),
)

FAIL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("error:", "command reported error"),
    ("fatal:", "command reported fatal error"),
    ("failed", "command reported failure"),
)


def _normalize_target_state(target_state: str | None) -> str | None:
    if target_state is None:
        return None
    normalized = target_state.strip().lower().replace("_", "-")
    return normalized or None


def _allowed_target_states(target_state: str | None) -> frozenset[str]:
    normalized = _normalize_target_state(target_state)
    if normalized is None:
        return DEFAULT_TARGET_STATES
    if normalized not in SUPPORTED_TARGET_STATES:
        return frozenset()
    return frozenset({normalized})


def classify_completion(
    *,
    exit_code: int,
    output: str,
    target_verified: bool = False,
    target_state: str | None = None,
) -> CompletionClassification:
    normalized = output.lower()
    if exit_code == 0:
        return CompletionClassification(
            CompletionOutcome.PASS,
            "command exited successfully",
            target_state=_normalize_target_state(target_state),
        )
    for phrase, reason in HARD_FAIL_PATTERNS:
        if phrase in normalized:
            return CompletionClassification(
                CompletionOutcome.FAIL,
                reason,
                phrase,
                target_state=_normalize_target_state(target_state),
            )
    if target_verified:
        allowed_target_states = _allowed_target_states(target_state)
        if not allowed_target_states:
            return CompletionClassification(
                CompletionOutcome.FAIL,
                f"unsupported already-done target state: {target_state}",
                target_state=_normalize_target_state(target_state),
            )
        for pattern in NO_OP_SUCCESS_PATTERNS:
            if pattern.phrase in normalized and pattern.target_states & allowed_target_states:
                return CompletionClassification(
                    CompletionOutcome.PASS_ALREADY_DONE,
                    pattern.reason,
                    pattern.phrase,
                    target_state=_normalize_target_state(target_state),
                )
    for phrase, reason in FAIL_PATTERNS:
        if phrase in normalized:
            return CompletionClassification(
                CompletionOutcome.FAIL,
                reason,
                phrase,
                target_state=_normalize_target_state(target_state),
            )
    return CompletionClassification(
        CompletionOutcome.FAIL,
        "non-zero exit without verified already-done target state",
        target_state=_normalize_target_state(target_state),
    )


def render_classification(classification: CompletionClassification) -> str:
    lines = [
        "PASS_ALREADY_DONE_CLASSIFICATION",
        f"outcome: {classification.outcome.value}",
        f"success: {'yes' if classification.success else 'no'}",
        f"reason: {classification.reason}",
    ]
    if classification.target_state:
        lines.append(f"target_state: {classification.target_state}")
    if classification.matched_phrase:
        lines.append(f"matched_phrase: {classification.matched_phrase}")
    lines.append(f"### RESULT: {'PASS' if classification.success else 'FAIL'} ###")
    return "\n".join(lines)


def classify_file(
    path: Path,
    *,
    exit_code: int,
    target_verified: bool = False,
    target_state: str | None = None,
) -> CompletionClassification:
    return classify_completion(
        exit_code=exit_code,
        output=path.read_text(encoding="utf-8"),
        target_verified=target_verified,
        target_state=target_state,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pass-already-done")
    parser.add_argument("path", type=Path)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--target-verified", action="store_true")
    parser.add_argument("--target-state", choices=sorted(SUPPORTED_TARGET_STATES))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    classification = classify_file(
        args.path,
        exit_code=args.exit_code,
        target_verified=args.target_verified,
        target_state=args.target_state,
    )
    print(render_classification(classification))
    return 0 if classification.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
