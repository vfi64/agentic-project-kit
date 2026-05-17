# Idempotent Finalization Branch Guard Inspection

Branch: feature/idempotent-finalization-branch-guard-impl

## Latest commits

21518c5 Finalize state after idempotent PR create guard (#306)
2848cdf Document idempotent finalization branch guard (#305)
97ec9cd Finalize state after deterministic ns slice runner (#304)
c503d4d Add deterministic ns slice runner (#303)
5a262cf Finalize state after no direct main commit guard (#302)
1ed1168 Add no direct main commit guard (#301)
3f7acfb Document deterministic ns slice runner priority
0f6a18e Finalize state after ns up no-op idempotence hardening (#300)
ee6eb6d Handle no-op branches idempotently in ns up (#299)
40a5a7a Add idempotent PR create guard (#297)
a5965b6 Finalize state after ns up idempotence hardening (#296)
f37744f Handle already merged PRs idempotently in ns up (#295)

## Finalization-related references


## PR/create workflow references

ns:77:if [ "${1:-}" = "commit-guard" ]; then
ns:82:if [ "${1:-}" = "slice-runner" ]; then
tools/ns_slice_runner.sh:7:  printf "%s\n" "ERROR: missing plan file. Usage: ./ns slice-runner <plan-file>"
tools/ns_pr_create_or_skip.sh:50:  gh pr create --base "$BASE" --title "$TITLE" --body "$BODY" || STATUS=1
tests/test_repo_ns_entrypoint.py:232:    assert "gh pr create --base" in text
tests/test_repo_ns_entrypoint.py:252:    assert "slice-runner" in text
