# Site Content Boundary

This directory is reserved for curated explanatory content that cannot be
derived from repository metadata.

Technical facts such as package version, command count, command surfaces,
manifest identity, release state and future claim status must be generated from
repository sources or computed evidence, not duplicated here.

`claims.yaml` is curated content, but not a truth store. It defines claim text,
whether a claim is required, optional planned intent, and evidence bindings.
The generated site computes claim status during the build.

`tool_comparison.yaml` stores curated descriptions with official HTTPS sources
and review dates. External products need a fresh editorial source review when
their descriptions change; Kit metadata cannot establish their current behavior.
Do not infer quality rankings, cost savings or universal compatibility.
