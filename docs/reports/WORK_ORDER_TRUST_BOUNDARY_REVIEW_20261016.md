# Work-order trust-boundary review (2026-10-16)

Status: read-only review; evidence, not a rule change
Plan step: `kit-control-effectiveness-measurement` / `ai-work-order-trust-boundary-review` (`docs/planning/PROJECT_DIRECTION.yaml`)
Base: `main` at `42f1a67` (after PR #2515)
Negative tests: `tests/test_work_order_trust_boundary.py`

## Question

LLM-written work orders reach the maintainer's machine through the repository: a browser LLM writes an order file to a branch, and a local Kit command reads and executes it. This review asks which checks the Kit actually enforces on that path and where the enforced checks fall short of what the Kit's own rules and safety classes claim.

The review changes no runtime behaviour. Every gap below was confirmed by a probe in a temporary directory and is pinned by a strict-xfail test that asserts the safe behaviour. A hardening slice that closes a gap makes the test pass, and strict xfail then forces removal of the marker.

## Threat model

- **Trust root.** The Kit treats an order that is present on a branch it reads as authorised. Nothing in the order is authentication. In particular, `COMMAND_MANIFEST_ACK <sha>` proves only that the author knew the public manifest hash; it does not identify the author.
- **Actor.** The LLM that writes orders is assumed honest but fallible. It can be confused, outdated or manipulated by content it read (prompt injection). The Kit's checks are what stands between such an order and local execution.
- **Reach.** `transfer continue`, the canonical communication start, infers the order branch from every local and `origin/*` ref that holds an active order and runs it when exactly one exists (`transfer_continue._active_order_branches`). Push access to any branch on origin is therefore enough to place an order that the maintainer's next `transfer continue` executes.

## Ingestion paths

| Order file | Format | Executed by | Main checks |
|---|---|---|---|
| `.agentic/transfer/inbox/current.yaml` | transfer order: `write_text_file`, `run_command` | `transfer continue` → `transfer remote-next` → `run_local_transfer` → `apply_transfer_order`; also `transfer apply`, `transfer run-local` | status/kind/branch/freshness guard (only without `--branch`), clean worktree, safe-push target, `run_next_command` capability, repo-relative paths, shell-token and interpreter denylist, instruction lint with ACK |
| `.agentic/typed_work_orders/inbox/*.yaml` | typed order: `command_argv`, `cockpit_action` | `remote-next` / `rn` (after `git switch main` + pull), `work-order typed-next`, `work-order typed-run --execute` | exactly one queued order, no duplicate execution, dirty worktree blocks (order may disable it), `log_path` prefix |
| `.agentic/work_orders/<id>.yaml` | shell command string | `work-order run --execute` (`bash -lc`) | governance check, branch assertion, fragment denylist, required gate names, `log_path` prefix |
| `.agentic/commands/inbox/next-turn.py` | Python script | GUI work-order run (`run_validated_work_order`) | required phrases, text denylist, import denylist |
| fixed slot (`next_turn_runner`) | Python script | `python -m agentic_project_kit.next_turn_runner` | slot files exist; no content validation |
| `.agentic/commands/inbox/current.sh` | shell script | `agent_command_runner` (module entry point) | expected branch, `sh -n` syntax check |
| `.agentic/current_work.yaml` | step list | `tools/workflow_runner.py` via `workflow go/run` | allow-listed steps; branch names validated since PR #2514 |
| planner-executor intent | `command` / `cockpit_action` | `executor run --execute` | manifest-resolved commands only, direct commands READ_ONLY only, BOUNDED needs intent flag and `--allow-bounded`, DESTRUCTIVE blocked |

The planner executor is the reference design: authority comes from the generated command manifest and from a local CLI flag, never from the order alone.

## Checks that hold

Pinned by the unmarked tests in `tests/test_work_order_trust_boundary.py`:

- `run_command` refuses `bash`/`sh`/`zsh`/`fish`/`python`/`python3` as `argv[0]` and shell control tokens as argv items.
- The instruction lint blocks literal `git push`, `git commit`, `git branch -D`/`git push --delete` and `gh pr merge` (manifest `replaces_raw`), and unknown `agentic-kit` subcommands.
- A stale or missing ACK line blocks `transfer apply`.
- Transfer `target_path`/`payload_path`/`report_path` reject absolute paths, `..`, and the roots `.git`, `.venv`, `venv`, `__pycache__`.
- The planner executor runs no BOUNDED command directly and accepts only `agentic-kit` argv.
- Typed queue: more than one queued order, or an order already in `executed/`, is refused.

## Confirmed gaps

Severity is the impact when a confused or manipulated order reaches a branch the Kit reads.

| ID | Severity | Path | Gap | Probe result |
|---|---|---|---|---|
| WOTB-01 | high | typed orders | `command_argv` executes any argv. `safety: READ_ONLY` is a label and is not enforced. `remote-next`/`rn` and `typed-next` run the queued order without an `--execute` step. | `touch EXECUTED` ran under `safety: READ_ONLY` |
| WOTB-02 | medium | typed orders | `cockpit_action` passes the order's own `allow_bounded` to `run_cockpit_action`, so an order authorises its own BOUNDED actions, for example `dialog.rnc` (commit and push closeout paths) or `dialog.rn` (run the next order). | `allow_bounded=True` reached the cockpit call |
| WOTB-03 | medium | typed orders, `work-order run` | `log_path` is checked with `startswith("docs/reports/terminal/")` only; `docs/reports/terminal/../../../../x` writes outside the repository. | log file created outside the repository root for both runners |
| WOTB-04 | low | `work-order run` | The required gates are substring checks on the command; `echo pytest ruff check check-docs doctor; …` satisfies the contract without running a gate. This defeats the gate contract, not a security boundary, because the lane executes shell by design. | `check_work_order` returned no errors |
| WOTB-05 | medium | transfer `run_command` | Raw git/gh and interpreters are recognised only by literal `argv[0]` or text prefix. `env git push --force`, `/usr/bin/git push`, `git -c … push`, `git -C . push`, `env gh pr merge`, `/usr/bin/python3 -c`, `.venv/bin/python -c` pass parsing and lint; `git -c`/`git -C` produce only a WARN. This contradicts `transfer_safety_rules.yaml` ("Do not put raw gh … into LLM-to-local payloads"). | all seven argv vectors reach execution |
| WOTB-06 | high | transfer `write_text_file` | Paths are checked lexically; symlinks are followed. A payload symlink copies any readable file into the repository, where a later commit can publish it, and a symlinked directory makes the write land outside the repository. | secret copied into `docs/leak.txt`; file planted outside the root |
| WOTB-07 | medium | transfer freshness guard | `_head_matches` accepts any prefix of HEAD, including one character (`short_head.startswith(value)`), so an anchor matches about one HEAD in sixteen without any knowledge of the current state. | `_head_matches("a", …)` is true for a HEAD starting with `a` |
| WOTB-08 | high | `transfer remote-next` / `transfer continue` | (a) The freshness guard (status, kind, expected branch, anchor) runs only when no branch is given; `transfer continue` always passes the inferred branch, so on the canonical path the guard is skipped. (b) Without a branch, the guard validates the order in the current checkout, and the order executed is re-read after `git switch` and `git pull` of the order's branch, with no re-validation. | an order without status, kind or anchor executed with `branch=`; a different order executed than the one validated |
| WOTB-09 | low | `next-turn.py` lane | The validator is a text denylist over an arbitrary Python script (`'git push'`, `'os.system('`, …). `subprocess.run(["git", "push", …])` or `__import__("o"+"s")` pass. The lane is unrestricted by nature; the validator must not be presented as a safety boundary. | validator returned `ok=true` |

Additional observation, not a test: the manifest declares `work-order typed-next`, `typed-run`, `run`, `transfer apply` and `transfer run-local` with `remote_effects: none` and safety BOUNDED, but the order content decides what they execute, including pushes.

## Proposed findings and hardening order

Each line is a proposed finding with its own slice and regression test (the tests above). The owner decides order and scope.

1. **WOTB-06, WOTB-03: confine paths.** Resolve every order-controlled path, require it to stay under the repository root, and refuse symlinks for payloads and target parents. Use one helper for transfer, typed and shell orders; the planner executor's `_safe_evidence_path` covers parent segments but not symlinks.
2. **WOTB-08, WOTB-07: bind the executed order to the validated one.**
   - Run the guard on every path, including an explicit or inferred branch.
   - Re-read and re-validate the order after `switch`/`pull`, and refuse when its id or content hash differs.
   - Require a full 40-character anchor, or at least 12 characters.
   - Because a committed order cannot name its own commit, the anchor semantics (parent commit or order-blob hash) need an explicit decision.
3. **WOTB-01, WOTB-02, WOTB-05: command authority from the manifest, not from the order.**
   - Resolve typed `command_argv` and transfer `run_command` the way the planner executor does: manifest commands by safety class, with `.venv/bin/agentic-kit` treated as `agentic-kit`.
   - Allow-list read-only raw git (`git status`, `git branch --show-current`); existing typed orders use these.
   - Anything else, and every BOUNDED cockpit action, needs a local CLI flag.
   - Then correct the declared `remote_effects`.
4. **WOTB-04, WOTB-09: state the unrestricted lanes honestly or retire them.**
   - `work-order run` (bash) and the `next-turn.py`/`current.sh` lanes execute arbitrary code by design. Their validators must be documented as format checks.
   - The command usage audit (2026-10-15) shows no recorded use outside tests for `work-order run`, `typed-next`, `typed-run` or `remote-next`. That makes these lanes decomplexification candidates rather than hardening targets.

## Status after the first hardening slice (2026-10-16)

- **Closed:** WOTB-01, -02, -03, -05 and -06, by `order_paths.py` and `order_command_authority.py`. Their tests no longer carry xfail.
  - Typed `command_argv` and transfer `run_command` run READ_ONLY Kit commands and read-only `git`/`gh` queries.
  - BOUNDED Kit commands, BOUNDED cockpit actions and commands outside the manifest need the local `--allow-unlisted` flag on `transfer continue`, `transfer remote-next`, `transfer apply`, `transfer run-local`, `remote-next`/`rn`, `work-order typed-next` and `work-order typed-run`.
  - DESTRUCTIVE Kit commands, raw `git`/`gh` mutations and interpreters are refused even with the flag.
  - The refusal happens before any action of the order runs.
- **Closed in the second slice:** WOTB-07 and -08, by `order_freshness.py`.
  - The anchor must be a full 40-character hash. It must equal `HEAD` for an uncommitted order, and otherwise the first parent of the commit that last changed the order file.
  - `transfer remote-next` checks status, kind, branch and anchor again after switch and pull, on every path including an explicit or inferred branch (`transfer continue`). The order that runs is therefore the order that was checked.
  - `transfer order-validate` uses the same binding.
- **Decided, open:** WOTB-04/-09: the unrestricted lanes are retired with a deprecation window.

## Limits

- Probes ran against functions and against `run_remote_next_transfer` with git and reporting helpers replaced by fakes; no order ran against a live remote.
- The GUI paths were traced by code reading only.
- `agent_command_runner` (`current.sh`) was mapped but not probed; it runs a shell script by design (same class as WOTB-09).
- The review does not assess the remote side, meaning who can push which branch or how the browser LLM's repository access is scoped. That decides how reachable each gap is in practice.
