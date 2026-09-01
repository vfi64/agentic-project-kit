from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentWordBudgetResult:
    path: str
    words: int
    max_words: int | None
    warn_words: int | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def count_words(text: str) -> int:
    return len(text.split())


def evaluate_document_word_budget(
    path: str,
    text: str,
    *,
    max_words: Any = None,
    warn_words: Any = None,
) -> DocumentWordBudgetResult:
    words = count_words(text)
    errors: list[str] = []
    warnings: list[str] = []
    max_value = _coerce_positive_int(path, "max_words", max_words, errors)
    warn_value = _coerce_positive_int(path, "warn_words", warn_words, errors)

    if max_value is not None and warn_value is not None and warn_value >= max_value:
        errors.append(
            f"{path}: invalid word budget (warn_words {warn_value} must be below max_words {max_value})"
        )

    if max_value is not None and words > max_value:
        errors.append(f"{path}: too long ({words}/{max_value} words)")
    elif warn_value is not None and words >= warn_value:
        if max_value is None:
            warnings.append(f"{path}: word budget headroom low ({words} words; warn_words={warn_value})")
        else:
            remaining = max_value - words
            warnings.append(
                f"{path}: word budget headroom low ({words}/{max_value} words; "
                f"warn_words={warn_value}; remaining={remaining})"
            )

    return DocumentWordBudgetResult(
        path=path,
        words=words,
        max_words=max_value,
        warn_words=warn_value,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _coerce_positive_int(path: str, field: str, value: Any, errors: list[str]) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        errors.append(f"{path}: invalid {field} {value!r} (expected positive integer)")
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.append(f"{path}: invalid {field} {value!r} (expected positive integer)")
        return None
    if parsed <= 0:
        errors.append(f"{path}: invalid {field} {value!r} (expected positive integer)")
        return None
    return parsed
