# Post-v1.0.12 Greenfield Provenance Retest

Status: implemented external fixture pass  
Date: 2026-09-15  
Kit baseline: `origin/main` at `ee658e0d`  
Version context: `1.0.12`  
Machine-readable companion:
`docs/reports/POST_V1_0_12_GREENFIELD_PROVENANCE_RETEST_20260915.json`

## Scope

This slice retests the generated-versus-manual provenance contract behind
`KIT-GF-007` in a fresh temporary external workspace. The fixture was created
from the current checkout; it was not a PyPI installation and no published
package claim is made here.

## Evidence

The external fixture was initialized with:

```text
agentic-kit workspace init --root FIXTURE --name gf007-fixture --type generic --execute --json
```

The generated workspace contained the canonical provenance manifest:

```text
.agentic/dpa/workspace_init_projection.json
```

The fixture was then committed to obtain an exact validation ref and assessed
with:

```text
agentic-kit dpa repo-adoption-assessment --root FIXTURE --validation-ref EXACT_HEAD --json
```

Observed result:

| Measure | Result |
|---|---:|
| DPA result status | `READY_FOR_DPA_REPO_ADOPTION_ADJUDICATION` |
| blockers | `0` |
| generated or command-updated surfaces | `11` |
| manual preservation surfaces | `5` |
| generated surfaces requiring maintainer adjudication | `0` |
| exact validation ref | recorded |

All 11 generated projection surfaces were marked
`generated_projection`, `generated_or_command_updated: true`, and
`maintainer_adjudication_required: false`. Manual surfaces remained explicit
and retained their adjudication requirement.

## Finding adjudication

`KIT-GF-007` is closed for the current mainline implementation based on this
external fixture evidence. The closure is limited to the generated-versus-
manual DPA/adopt provenance contract; it does not imply automatic migration or
external-repository conformance.

`KIT-GF-017` remains open. Its required evidence is a fresh released-package
and external context-carrier retest, which is a separate validation slice.

## Boundaries

- This is current-checkout external-fixture evidence, not PyPI evidence.
- No production repository was mutated.
- No Greenfield finding beyond `KIT-GF-007` is closed by this report.
- The historical `POST_V1_0_10_GREENFIELD_REMAINING_FINDINGS_20260908`
  report remains unchanged as historical evidence.
