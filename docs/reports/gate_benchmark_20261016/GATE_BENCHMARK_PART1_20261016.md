# Gate benchmark, part 1: fault injection in an offline sandbox (2026-10-16)

Status: evidence; part 1 of plan step `gate-and-context-benchmark` (`docs/planning/PROJECT_DIRECTION.yaml`)
Harness: `run_gate_benchmark.py` in this directory
Results: `GATE_BENCHMARK_PART1_RESULTS.json` (Kit `main` after this slice), `GATE_BENCHMARK_PART1_BASELINE_1.0.25.json` (Kit 1.0.25 at tag `v1.0.25`)

## Question

Do the Kit gates catch the faults they claim to catch, without firing on a clean repository, and what does a check cost? Part 1 answers this deterministically, without an LLM. Part 2, a comparison of current against task-specific context with a real LLM and repetitions, follows later.

## Method

- **Sandbox:** A bare clone serves as `origin` and a working clone sits in a temporary directory. Nothing reaches the real repository or GitHub, and the invocation ledger is off.
- **Per scenario:** First a control run of the gate on the clean sandbox, then a run with one injected fault.
- **Counting:** A scenario counts as **detected** only when two things hold: the control run exits 0 without the fault marker, and the fault run shows the marker. A gate that always fails therefore detects nothing.
- **Repetitions:** Each scenario runs once; the runs are deterministic.
- **Denominator:** The 11 scenarios in the harness.
- **Comparison:** The same harness runs against the Kit before today's hardening: a sandbox at `v1.0.25`, with Kit 1.0.25 from PyPI.

## Scenarios and results

| ID | Fault class | Injected fault | Gate | 1.0.25 | `main` | Gate time with fault (`main`) |
|---|---|---|---|---|---|---|
| S01 | stale command authority | transfer order with a stale `COMMAND_MANIFEST_ACK` | `transfer apply` | detected | detected | 0.4 s |
| S02 | raw git bypass | `run_command: env git push --force origin main` | `transfer apply` | **ran** (rc 0) | detected | 1.0 s |
| S03 | path escape | payload is a symlink to a file outside the repository | `transfer apply` | **copied the file** (rc 0) | detected | 1.1 s |
| S04 | stale order | committed order with a 7-character anchor | `transfer remote-next <branch>` | control crashed (ScannerError) | detected | 2.2 s |
| S05 | order self-authorisation | typed order runs `touch` without `--allow-unlisted` | `work-order typed-run --execute` | **ran** (rc 0) | detected | 0.6 s |
| S06 | projection drift | handoff `release` block says 0.4.13 (HD-08 class) | `audit-drift-signals` | not applicable: neither the gate nor the injection point existed | detected | 0.6 s |
| S07 | stale entrypoint | `AGENTS.md` with a stale manifest ACK | `audit-command-authority` | detected | detected | 0.6 s |
| S08 | invalid planning state | plan item with an unknown status | `direction validate` | detected | detected | 0.8 s |
| S09 | unregistered document | new runbook under `docs/workflow/` | `doc-registry check-unregistered --strict-scope` | detected | detected | 0.8 s |
| S10 | direct git mutation | `git push` added to `tools/next-step.py` | `pytest tests/test_workflow_git_mutation_authority.py` | gate absent | detected | 1.9 s |
| S11 | commit on main | `transfer commit` on `main` | `transfer commit` | detected | detected | 1.1 s |

**Totals:**
- Kit `main`: 11 of 11 detected, 0 false positives on the clean control, 11 s of gate time.
- Kit 1.0.25: 5 of the 10 injectable scenarios detected. In S02, S03 and S05 the fault actually ran, and S04's control crashed.

## Findings

1. **Remote-next could not complete any ACK-headed order. This was pre-existing and is fixed in this slice.**
   - In the clean control of S04, every `transfer remote-next` run crashed with a `ScannerError`, before today's changes too (1.0.25 run).
   - The cause: the instruction lint requires `COMMAND_MANIFEST_ACK` as the first line, and `remote_next_order_contract` writes it there. But the remote-next guard, the report-path recovery and `transfer continue` read the inbox as raw YAML.
   - An order without the ACK passed those readers, and the lint then refused it. So no order could get through `transfer remote-next`.
   - All four readers now strip the ACK line. Invalid YAML is reported as a `ValueError`, not a traceback. `tests/test_transfer_order_ack_header.py` fails on the old code.
   - S04's control now runs end to end: `transfer remote-next` applies a committed order with a full anchor on its own branch and exits 0.
2. **The difference to 1.0.25 matches today's hardening.** S02, S03 and S05 are WOTB-05, WOTB-06 and WOTB-01 from `docs/reports/WORK_ORDER_TRUST_BOUNDARY_REVIEW_20261016.md`. In 1.0.25 the injected fault actually ran.
3. **Detection here is close to by construction.** The scenarios are faults the gates claim to cover. The benchmark tests those claims and false positives, not unknown faults. A detection share of 1.0 says nothing about faults outside the scenarios.
4. **Cost:**
   - A single gate takes 0.4–2.2 s; the whole harness run takes about 54 s, mostly building the sandbox.
   - For comparison, `doctor` starts about 20 Kit processes (invocation ledger, 2026-10-16), and one `work finish` ran 52 Kit invocations in 8.6 minutes.

## Reproduction

```bash
python docs/reports/gate_benchmark_20261016/run_gate_benchmark.py --out results.json
python -m venv /tmp/kit125 && /tmp/kit125/bin/pip install "agentic-project-kit==1.0.25" pytest
python docs/reports/gate_benchmark_20261016/run_gate_benchmark.py --ref v1.0.25 --kit-bin /tmp/kit125/bin --out baseline.json
```

The `main` results were produced with the repository's editable install, which includes this slice's ACK-header fix, in a sandbox cloned from `0497622`.

## Limits

- Only faults the gates are known to target are covered. New fault classes need new scenarios.
- No GitHub, CI or release gates are exercised; they need network and are out of scope for part 1.
- Wall times come from one cloud container and are only roughly comparable with the Mac.
