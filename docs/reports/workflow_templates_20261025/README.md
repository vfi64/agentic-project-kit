# Reviewed responsive workflow figures

Date: 2026-10-25. Base: `52586722444796075d36eecd98cefbc749e9202e`.

The owner supplied six reviewed SVG layouts and authorized their integration.
The templates retain the supplied visual design, with precise failure, memory and
publication boundaries. Source-bound cells replace facts embedded in artwork.
The figure projection records source hashes. No product workflow changed.

- G2: default work-finish merge path, successful-plan prechecks, explicit execute,
  PASS/BLOCKED and rc 2. Diagnostics can still run after a diagnostic failure.
- G3: five generated package files; handoff does not rely on chat memory.
  A failed package requires diagnosis, cause correction and revalidation.
- G0: the unique observed `finish work` root, 14 ordered direct callback entries,
  31 descendants of pr-create-complete and four rule acknowledgements. K0c's
  historical static validator witnesses are a separate binding, not runtime proof.

The historical offline receipts and their source revision are unchanged. No new
simulation, model call, live release or publication was performed.

## Validation

Targeted mutation tests cover state/default/return-code drift, exact sequence
changes, computed descendant counts, package shape and SVG slot drift. The
regenerated fallback is checked for staleness. Full-suite and gate results will
be recorded before closeout.

Browser QA used the generated page in a 1280-pixel desktop window and 390-pixel
iframe viewports, not standalone SVG previews alone. Desktop G0/G2/G3 and mobile
G0/G2/G3 were visually inspected. Expandable text was opened successfully.
Overview, Understand, Quickstart and Workflows each measured clientWidth=390 and
scrollWidth=390. Figure images measured 356 px and selected the mobile assets.
The test found existing mobile grid/long-inline-code overflow; minmax(0, 1fr)
and inline-code wrapping fix it without hiding content. Tables/pre blocks retain
local scrolling. This is one browser/viewport check, not universal device coverage.
