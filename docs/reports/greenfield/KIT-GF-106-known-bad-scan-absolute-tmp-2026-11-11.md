# KIT-GF-106: Known-bad scan below an outer tmp directory

Date: 2026-11-11

Scope: `_known_bad_pattern_scan` in `cli_commands/transfer_diagnostics.py`.

Status: fixed on the review branch; not merged or released.

## Finding

The excluded-directory filter inspected every component of an absolute file
path. If the project itself lived below a directory named `tmp`, an active
pattern in `src/` produced zero matches. The existing historical-planning-doc
test asserted only an empty result, so it could not reveal this false negative.

## Change

The filter now inspects the path relative to the project root. An internal
`tmp`, `.venv`, `.git` or `__pycache__` remains excluded. A source search for
`file_path.parts` showed this was the only source occurrence of this filter.

## Regression evidence

`test_known_bad_scan_finds_source_below_outer_tmp_component` failed before the
fix (0 matches instead of 1) and passes after it. The companion
`test_known_bad_scan_skips_internal_tmp_and_venv` preserves exclusions.

## Boundaries

The report describes native tests, not an external consumer retest. The
installed-runtime retest harness has no outer-tmp project fixture. No release
or consumer `VERIFIED_FIXED` is claimed.
