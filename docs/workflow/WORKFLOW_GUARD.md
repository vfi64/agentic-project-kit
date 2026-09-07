Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Workflow Guard

The workflow guard is a machine-checkable diagnostic layer for recurring workflow errors. It starts in diagnose-and-fail mode and blocks further mutation when protected control files lose required anchors, governance YAML stops parsing, or known bootstrap drift appears.

The guard also enforces the patch-cycle diagnostic gate. When repo-backed command
reports or local `tmp/` evidence show two patch/test failures in the same patch
family without a later diagnosis marker, the guard reports
`next_mutation_allowed=false` and blocks a third mutation until bounded diagnosis
evidence exists.

Safe changes must be narrow and evidence-backed. Semantic rule loss, release-state conflict, broad document rewrite, and unclear YAML recovery require review and a repair plan before further mutation.
