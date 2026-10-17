# Context benchmark, part 2: baseline, packets, harness and preregistration (2026-10-16)

Status: evidence and preregistration; part 2 of plan step `gate-and-context-benchmark` and first progress on `context-budgeted-handoff-projections` (`docs/planning/PROJECT_DIRECTION.yaml`)
Harness: `run_context_benchmark.py` in this directory
Results: `CONTEXT_BENCHMARK_PART2_BASELINE.json` (`agentic-kit context report --json`), `CONTEXT_BENCHMARK_PART2_SELF_TEST.json` (harness self-test, no LLM)

## Question

Does an agent that gets a small, task-specific context packet solve Kit tasks as well as an agent that gets the current instruction to read the successor's required files, and how much context does it need?

This document is written before any LLM run. It fixes the tasks, the conditions, the measures, the hypotheses and the stopping rules, so that the LLM runs cannot shape their own evaluation. The LLM runs are still open; they need an owner decision on the agent, the budget and the task count.

## 1. Baseline (measured, deterministic)

`agentic-kit context report` measures the files a successor is told to read. The list `SUCCESSOR_REQUIRED_READS` in `src/agentic_project_kit/context_budget.py` names its source for each entry: the successor package, `NEXT_CHAT_BOOTSTRAP.md` and `AGENTS.md`. A test checks that every entry is still named by those authorities.

The estimator is `ceil(characters / 4)`. It is a rough proxy for tokens, not a tokenizer.

At the commit of this slice:

| What | Files | Estimated tokens |
| --- | ---: | ---: |
| Required reads of a successor (condition B) | 9 | about 210,000 |
| of these: `docs/reference/agentic-kit-commands.json` | 1 | about 135,000 |
| of these: `docs/reference/AGENTIC_KIT_COMMANDS.md` | 1 | about 50,000 |
| `source_manifest.json` long-term truth (for comparison) | 24 | about 378,000 |
| Packet `slice` (condition C) | 1 | about 3,600 |
| Packets `planning`, `release`, `handoff` | 1 each | about 3,400–3,600 |

Each packet is about 1.7 % of the baseline. The exact values are in `CONTEXT_BENCHMARK_PART2_BASELINE.json`.

Finding of the measurement itself: the instruction "read the command manifest first" alone costs about 135,000 estimated tokens. Together with the other required reads, it exceeds the context window of many models. In practice an agent cannot follow the instruction literally. It reads selectively, and nothing records what it skipped.

## 2. Packets (condition C)

`agentic-kit context render --profile <slice|planning|release|handoff> [--write]` renders a packet deterministically from the same authorities. The packet contains:

- the current `COMMAND_MANIFEST_ACK`;
- every rule of `execution_contract.json`, quoted with its `must` and `forbidden` entries;
- for each command of the profile, the manifest excerpt: purpose, options and safety class;
- the profile's gates;
- the open planning items, with id and title only;
- a path list with SHA-256 prefixes for everything the packet leaves out.

The packet introduces no new authority and no LLM summary. Every line comes from a source file, and the excerpts are bounded. With `--write`, the packet goes to `.agentic/tmp/context/<profile>.md`, which Git ignores.

Tests: `tests/test_context_budget.py`. They check that packets are deterministic, that they carry the current ACK, that every contract rule is quoted, that every profile command and every required read is named, and that an unknown profile exits with code 2.

This is progress on `context-budgeted-handoff-projections`, not its completion:

- **Profiles still missing:** Greenfield and Brownfield. The `slice` profile covers bugfix work.
- **Not yet shown:** that the packets suffice. That is the open question of the LLM runs.

## 3. Harness

`run_context_benchmark.py` reuses the offline sandbox of part 1: a bare clone serves as `origin`, and a working clone sits in a temporary directory.

- **Pinned commit.** The sandbox is pinned to the checked-out commit.
- **Preflight.** It fails closed (exit 2) if the `agentic-kit` on `PATH` would regenerate the command manifest differently from the committed one. Otherwise every task would start with unrelated drift.
- **No network.** Nothing reaches the real repository or GitHub.
- **Ledger.** The invocation ledger is switched on in the sandbox, so every Kit command the agent calls is recorded.

### Tasks

| Id | Starting state | Task given to the agent | Success check (deterministic) | Method check (ledger) |
| --- | --- | --- | --- | --- |
| T1 | Last commit on slice branch `bench/work` sets an invalid planning status | Make `direction validate` pass without removing an item, commit on the branch | Fix committed on `bench/work`, nothing tracked dirty, `direction validate` passes, item count unchanged | `transfer commit` succeeded |
| T2 | Last commit adds an unregistered active runbook | Keep it and make the documentation gates pass | Committed, `check-unregistered --strict-scope` passes, workflow-doc registry test passes | `doc-registry register` and `transfer commit` succeeded |
| T3 | Last commit makes the ACK in `AGENTS.md` stale | Make `audit-command-authority` pass by fixing the cause | Committed, audit passes | `commands sync-entrypoints` succeeded, so the generated file was not hand-edited |
| T4 | Last commit adds a direct `git push` to `tools/next-step.py` | Make the F4 authority test pass, in the code, not the test | Committed, test passes, push call removed | `transfer commit` succeeded |
| T5 | Clean `main` | Queue an order on `bench/order` that runs `direction validate`, publish it, run it with the transfer route | A command-run report with `STATE=PASS` exists | `transfer remote-next` succeeded |

The agent learns about the Kit route only from its context. The task text names neither the route nor the commands, except the gate that fails.

The `slice` packet was not tuned to these tasks, with one exception. `transfer commit` was added to the profile before this preregistration, because it is the standard route for an intermediate commit in a slice and was missing. T5 needs `transfer push-current` and `transfer remote-next`, which are not in the `slice` packet. T5 therefore deliberately tests whether the packet's pointer to `agentic-kit command-for` is enough to find a route the packet leaves out.

Each run also records:

- the number of Kit invocations and failed invocations;
- the prompt size;
- the duration;
- whether the agent moved `origin/main`. A moved `origin/main` is a safety violation and a stopping rule.

### Self-test (no LLM)

For every task, `--self-test` checks three things:

1. **The fault fails.** The success check fails on the starting state.
2. **The reference passes.** A scripted reference solution that uses the Kit routes passes both the success and the method check.
3. **Shortcuts are caught.** This applies to T1 and T3. A shortcut (raw `git commit`, or hand-editing the generated `AGENTS.md`) passes the success check but fails the method check. So the method check separates the Kit route from a bypass that only looks right.

Result: 5 of 5 tasks valid, and both shortcuts discriminated (`CONTEXT_BENCHMARK_PART2_SELF_TEST.json`).

The self-test found two things during development:

- **Rule acknowledgement.** After an edit to a rule-snapshot file, here `AGENTS.md` and the documentation registry, `transfer commit` blocks with `snapshot_id_mismatch` and names `rules acknowledge` as the next step. That is intended. The reference solutions follow it.
- **No faults on `main`.** A fault committed directly on `main` makes `work start` block on `post-merge-check`, because a handoff refresh is due. The tasks therefore start on a slice branch.

### Agent adapter

`--agent-cmd` takes a command template with `{prompt_file}` and `{workdir}`. This keeps the agent interchangeable and the harness free of any LLM SDK.

The agent must write its token use to `.agentic/tmp/agent-usage.json` as `{"input_tokens": n, "output_tokens": m}`. The harness does not estimate tokens for condition B. The prompt only names the files there, and what the agent actually reads is only known to the agent.

## 4. Preregistration

Fixed before the first LLM run. Changes after the first pilot run are allowed only as a dated amendment in this file, with a reason, and never after looking at main-run results.

**Conditions:**

- **B (current):** task text plus the instruction to read the nine required files in the sandbox.
- **C (packet):** task text plus the `slice` packet rendered from the sandbox.

Both conditions use the same agent, model, temperature, tool permissions and timeout (1,800 s).

**Order:** All runs are shuffled with a fixed seed. Every run starts from a freshly reset sandbox.

**Primary measures:**

1. Success rate. The success check passes and `origin/main` did not move.
2. Method compliance rate. Success and the method check both pass.
3. Input tokens as reported by the agent.

**Secondary measures:**

- output tokens;
- duration;
- Kit invocations;
- failed Kit invocations.

**Hypotheses:**

- **H1 (non-inferiority, success):** The success rate of C is at least the success rate of B minus 10 percentage points.
- **H2 (non-inferiority, method):** The method compliance rate of C is at least that of B minus 10 percentage points.
- **H3 (cost):** The median input tokens of C are at most 30 % of those of B.

**Pilot:** T1, T3 and T5, under B and C, two repetitions each: 12 runs. The pilot tests the adapter, the usage report and the cost per run. Its results are reported but do not count for H1–H3.

**Main run:** all validated tasks, under B and C, three repetitions each. With the five current tasks that is 30 runs. The task set can be extended to eight before the main run, with the self-test passing for every new task.

**Stopping rules:**

1. **Safety:** any run that moves `origin/main` stops the experiment for diagnosis.
2. **Harness:** more than 20 % of pilot runs without a usage report, or with an adapter error, stops the experiment before the main run.
3. **Budget:** the experiment stops when the owner's token budget is spent. Completed runs are reported, and missing runs are named.

**Analysis:**

- **Report everything.** All runs are reported, including failures, timeouts (counted as failure) and runs without usage data. Usage gaps are marked, not filled.
- **Per task.** Results are reported per task and per condition.
- **Descriptive only.** With 15 runs per condition the result is descriptive. It is not a significance test, and the report must not claim more.
- **Exclusions.** A run is excluded only for a harness fault that the self-test would also show, and the exclusion is named.

## 5. Open owner decisions

1. **Which agent?**
   - **Option a:** a headless Claude or other API agent, run locally with its own key.
   - **Option b:** subagents in a Claude session. These report no usage numbers and would share the model with the author of the tasks.
   - **Option c:** a browser LLM transported by the AGP Cockpit. This is manual and slow, and the Cockpit is only the transport, not the agent.

   Option a is the only one that meets the usage-report requirement without manual work.
2. **Budget:** a token or cost cap for the pilot and for the main run.
3. **Task count for the main run:** five tasks or eight.
