# KIT-GF-098: Return targets the exact previous pinned Kit version

Consumer: an external desktop controller. Status: implemented and locally verified; fixed_in remains unreleased.

The return target was previously fixed to 1.1.10. It now comes from the validated prior CI pin in the original adoption receipt; prior installation identity is retained separately, and an available original wheel hash must match.

Release A keeps `EXTERNAL_PROJECTION_V2_ACTIVE = False`: external generation/checks retain v1, init adds no minimum, and target probes do not confuse module presence with activation. A later separately approved B changes the single package constant to True. GF-094 remains PARTIAL in A; GF-096 expiry starts from B. Known external workspaces adopt A first; B1 additionally waits for recorded cycle 008. No environment/workspace switch was added.

The real transition matrix uses distinct source-built test wheels A=1.1.11, B=1.1.12 and A-prime=1.1.11.post1, loopback resolution, actual pip installation, owned runtimes and real local bare-origin squashes. Only PR observation is a test double. A plans and executes B, writes migration and adoption evidence, and B passes fresh check/doctor and post-merge check after later product work without a refresh. B prepares the exact revert, the actual squash is verified, return installs A, original bytes match and unrelated product work survives. A generates v1 and A-to-A-prime performs no projection migration.

For the direct legacy-to-B case, only unsupported preview is simulated. Actual B installation first ends BLOCKED without an adoption receipt; B check identifies missing migration. Existing prepare-successor-handoff followed by the repeated B update yields empty changed_paths and check/doctor PASS. Missing original adoption evidence explicitly blocks installation return; it is never reconstructed or guessed.

Return remains bound to exact PR/squash identity, original receipt, file hashes, the prior pin and signed staged artifact hashes. When the original installation recorded that pin's wheel hash, another wheel with the same version is rejected. Unknown original hashes are not claimed verified. Normal downgrade prohibition remains. Pending return does not bypass main-branch, upstream or clean-worktree guards and never auto-migrates restored v1.

Validation at source revision `f575952877890a4b4a115e9c71eb1eaea3355fc9`:

| Check | Result |
|---|---|
| `python -m pytest -q -n 4` | 4505 passed; 307.29 s; 560 warnings |
| `ruff check .` | PASS |
| `agentic-kit check --json` | PASS |
| `agentic-kit check-docs` | PASS |
| `agentic-kit doctor` | PASS |
| Fresh noneditable-wheel GF-094/095/097/098 contracts | Four PASS; historical v2 fixtures explicitly activate B |

Regression tests first reproduced missing activation policy, wrong target probing, missing normal-update receipts, the fixed return version, absent original-artifact enforcement and pending-return branch bypass. Existing Safe-Push and remote-effect audits remain unchanged. Active fixture origins use the established confined local-fetch construction.

The [first CI run](https://github.com/vfi64/agentic-project-kit/actions/runs/41322902179) exposed a Linux exec-argument limit that the macOS runs did not: passing the large captured projection JSON as one argument failed before target execution. The correction passes the same JSON through a private temporary file outside the workspace. Its regression first reproduced an oversized argument, then verified bounded argv, exact input bytes and cleanup. The full suite and fresh-wheel contracts above include this correction. Remote CI success is read from the current PR checks, never inferred from local PASS.

Complexity balance: three focused modules provide the activation policy, disposable wheel construction and transition matrix. Existing update, generation, return and governance routes are reused; no new CLI route, dependency, environment flag, workspace flag or generic rollback framework. `greenfield_retest.py` retains its existing fixture-dispatch adapter; its mixed runner responsibilities remain a known monolith risk. A future approved slice can extract fixture dispatch without changing contracts. Existing typed plans, receipts and result JSON are sufficient; another DCO cell layer would add complexity here.

Independent consumer rehearsal: NOT_RUN. Owner acceptance: PENDING. No release, merge, productive consumer migration or Self-hosting stage 2. No measured CI/runtime reduction is claimed. Historical approvals and evidence remain unchanged. Full machine fields and the local wheel hash are in the adjacent JSON report.
