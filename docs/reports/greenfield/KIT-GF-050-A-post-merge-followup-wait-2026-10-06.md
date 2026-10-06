# KIT-GF-050 A — post-merge follow-up CI wait

- `pr-complete --timeout-seconds` now forwards its CI budget to `post-merge-complete`.
- A follow-up CI timeout is reported as `PENDING` with the refresh PR number.
- `pr-complete` recognizes that pending result and stops before recovery/fallback actions.
