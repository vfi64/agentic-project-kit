Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Workflow Guard

The workflow guard is a machine-checkable diagnostic layer for recurring workflow errors. It starts in diagnose-and-fail mode and blocks further mutation when protected control files lose required anchors, governance YAML stops parsing, or known bootstrap drift appears.

Safe changes must be narrow and evidence-backed. Semantic rule loss, release-state conflict, broad document rewrite, and unclear YAML recovery require review and a repair plan before further mutation.
