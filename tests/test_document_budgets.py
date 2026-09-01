from agentic_project_kit.document_budgets import evaluate_document_word_budget


def test_document_word_budget_warns_without_failing_below_max() -> None:
    result = evaluate_document_word_budget("README.md", "one two three", max_words=5, warn_words=3)

    assert result.ok
    assert result.words == 3
    assert result.errors == ()
    assert result.warnings == (
        "README.md: word budget headroom low (3/5 words; warn_words=3; remaining=2)",
    )


def test_document_word_budget_blocks_hard_limit() -> None:
    result = evaluate_document_word_budget("README.md", "one two three four", max_words=3, warn_words=2)

    assert not result.ok
    assert result.errors == ("README.md: too long (4/3 words)",)
    assert result.warnings == ()


def test_document_word_budget_rejects_warn_at_or_above_max() -> None:
    result = evaluate_document_word_budget("docs/STATUS.md", "one two", max_words=5, warn_words=5)

    assert not result.ok
    assert result.errors == (
        "docs/STATUS.md: invalid word budget (warn_words 5 must be below max_words 5)",
    )
