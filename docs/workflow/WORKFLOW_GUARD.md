# Workflow Guard

The workflow guard is a machine-checkable diagnostic layer for recurring workflow errors. It starts in diagnose-and-fail mode and blocks further mutation when protected control files lose required anchors, governance YAML stops parsing, or known bootstrap drift appears.

Safe changes must be narrow and evidence-backed. Semantic rule loss, release-state conflict, broad document rewrite, and unclear YAML recovery require review and a repair plan before further mutation.

## Partial fetch full replacement guard

The standard failure class `partial-fetch-full-replacement-corruption` is a hard workflow defect. A line-range fetch, search result snippet, PR file patch, diff hunk, truncated API response, or copied chat excerpt is read-only context. It must not be used as the complete source for a full-file replacement.

Full-file replacement of a protected control file is allowed only from a complete raw fetch without line limits, complete blob content, local complete file content, or a generated file from a canonical source model. The reviewer-visible summary must identify that source when the replacement touches a protected file.

Protected files also have a deletion budget. A large protected-file deletion diff without an explicit control-file migration is blocked before merge. The migration path must name removed anchors, successor anchors, rationale, and deterministic test coverage.

This guard is intentionally conservative. It cannot prove semantic correctness, but it catches the dangerous class where a partial API result is accidentally treated as the whole file and where a generic YAML dump rewrites a protected control file with noisy or lossy changes.
