from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CompletionOutcome(str, Enum):
    PASS = "PASS"
    PASS_ALREADY_DONE = "PASS_ALREADY_DONE"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CompletionClassification:
    outcome: CompletionOutcome
    reason: str
    matched_phrase: str | None = None

    @property
    def success(self) -> bool:
        return self.outcome in {CompletionOutcome.PASS, CompletionOutcome.PASS_ALREADY_DONE}


NO_OP_SUCCESS_PATTERNS: tuple[tuple[str, str], ...] = (
    ("nothing to commit, working tree clean", "git commit target state already clean"),
    ("nothing to commit", "git commit target state already clean"),
    ("working tree clean", "worktree already clean"),
    ("everything up-to-date", "remote already up to date"),
    ("already up to date", "local branch already up to date"),
    ("already exists", "target already exists"),
    ("a pull request for branch", "pull request already exists"),
    ("pull request already exists", "pull request already exists"),
    ("no changes to commit", "no changes to commit"),
)

FAIL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("error:", "command reported error"),
    ("fatal:", "command reported fatal error"),
    ("traceback", "python traceback"),
    ("failed", "command reported failure"),
)


def classify_completion(*, exit_code: int, output: str, target_verified: bool = False) -> CompletionClassification:
    normalized = output.lower()
    if exit_code == 0:
        return CompletionClassification(CompletionOutcome.PASS, "command exited successfully")
    if target_verified:
        for phrase, reason in NO_OP_SUCCESS_PATTERNS:
            if phrase in normalized:
                return CompletionClassification(CompletionOutcome.PASS_ALREADY_DONE, reason, phrase)
    for phrase, reason in FAIL_PATTERNS:
        if phrase in normalized:
            return CompletionClassification(CompletionOutcome.FAIL, reason, phrase)
    return CompletionClassification(CompletionOutcome.FAIL, "non-zero exit without verified already-done target state")


def render_classification(classification: CompletionClassification) -> str:
    lines = [
        "PASS_ALREADY_DONE_CLASSIFICATION",
        f"outcome: {classification.outcome.value}",
        f"success: {'yes' if classification.success else 'no'}",
        f"reason: {classification.reason}",
    ]
    if classification.matched_phrase:
        lines.append(f"matched_phrase: {classification.matched_phrase}")
    lines.append(f"### RESULT: {'PASS' if classification.success else 'FAIL'} ###")
    return "\n".join(lines)


def classify_file(path: Path, *, exit_code: int, target_verified: bool = False) -> CompletionClassification:
    return classify_completion(exit_code=exit_code, output=path.read_text(encoding="utf-8"), target_verified=target_verified)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pass-already-done")
    parser.add_argument("path", type=Path)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--target-verified", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    classification = classify_file(args.path, exit_code=args.exit_code, target_verified=args.target_verified)
    print(render_classification(classification))
    return 0 if classification.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
