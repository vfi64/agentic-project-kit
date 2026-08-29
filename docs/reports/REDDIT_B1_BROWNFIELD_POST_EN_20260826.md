# Reddit Draft: Brownfield B1 Result

Status: final draft, not posted
Date: 2026-08-26
Evidence base:
`docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.md` and
`docs/reports/POST_V1_0_6_B1_RULE_ACK_RELEASED_PACKAGE_RETEST_20260826.md`;
post-v1.0.7 merge-wrapper correction:
`docs/reports/POST_V1_0_7_B1_COMM_SCI_CYCLE_006_MERGE_WRAPPER_RETEST_20260829.md`

## Possible Titles

- I took my repository-governance tool back to the brownfield Python project that made me build it
- Five real brownfield cycles after three and a half months of self-hosting
- How much autonomy can a repository safely grant to a coding agent?

## Draft

Three and a half months ago, a Python project of mine had grown complex enough
that I could no longer reliably carry its architectural state across LLM
sessions. That problem eventually pushed me to build a file-backed repository
governance system.

After months of mostly developing and testing that system on itself, I recently
took it back to the repository that had triggered the whole project.

The question was simple: could the generalized system now operate safely inside
the kind of brownfield repository that had made me build it in the first place?

The result is mixed in the useful way. I ran five real maintenance cycles in the
brownfield repo. They were not toy tasks: the work removed legacy seams in an
existing application and later adjusted the target repository's CI so PRs
against its integration branch had real checks.

Measured result:

- five real maintenance cycles;
- four merge-boundary cycles;
- legacy seams went from 72 to 58;
- full-suite runs stayed green across the cycles that ran them, growing from
  1,483 to 1,490 tests as regression coverage was added;
- Cycle 005 changed CI configuration rather than application code, so it has no
  historical full-suite entry and is counted through remote CI evidence;
- the process found four Kit defects in external core paths that self-hosting
  had not exposed.

Those defects mattered. One was packaging: the installed package did not include
the command manifest resource, so manifest-dependent commands were brittle in an
external workspace. Another was merge preflight leaking self-hosting assumptions
into a foreign repo. A third assumed `main` for post-merge checks even though the
target branch was an integration branch. The fourth was rule acknowledgement:
external workspaces needed target-owned rule sources instead of the Kit's own
self-hosting rule files.

Three of those fixes shipped in 1.0.5 and were retested from a PyPI install.
The rule-ack fix shipped in 1.0.6; a targeted PyPI retest on the adopted
Comm-SCI integration branch shows external rule-source validation and rule
acknowledgement passing. I am not counting that as a sixth maintenance cycle or
as a new full merge-wrapper retest.

The merge story is better than the original closeout could claim. During B1,
after the target repo got real remote CI, the safe merge wrapper did merge the
PRs, but the local wrapper did not return cleanly after a successful remote
merge. A later Comm-SCI retest against the published 1.0.7 package closed that
specific follow-up: `pr-merge-safe` returned terminal PASS in 8.034 seconds
after a real external remote merge. The remaining external friction is narrower:
generated Rule-Ack state can still block merge preflight as local dirty state.

So the claim is deliberately narrow:

Five real brownfield maintenance cycles provide evidence beyond self-hosting,
but one familiar private repository is not enough to establish general
brownfield portability.

The public website now leads with workflow choice rather than a giant command
list: File Transfer, Copy and Paste, Agent Direct, and an experimental GUI
surface. It also shows the Brownfield evidence boundary instead of claiming
"brownfield support proven".

The Kit itself makes no LLM API calls and does not require an LLM API. It also
does not replace Git, GitHub, CI, or AGENTS.md-style instructions. Git records
history, GitHub coordinates review, CI validates configured checks, and
instructions guide an executor. The Kit's role is to keep durable operational
state, governance, evidence, command metadata, and handoffs in the repository so
work can continue across sessions, models, and interfaces.

The question I am left with is:

How much autonomy can the repository safely grant given the evidence currently
available?

Related questions I would genuinely like opinions on:

- Where do you draw the boundary between coding-agent autonomy and
  repository-changing operations?
- How do you preserve operational context across sessions, models, and
  interfaces without making one agent runtime the source of truth?
- If this looks overengineered, which part would you remove first without losing
  the safety property it provides?

Links:

- Project site: https://vfi64.github.io/agentic-project-kit/
- Repository: https://github.com/vfi64/agentic-project-kit
- PyPI 1.0.7: https://pypi.org/project/agentic-project-kit/1.0.7/
- B1 evidence closeout:
  https://github.com/vfi64/agentic-project-kit/blob/main/docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.md
- 1.0.7 merge-wrapper retest:
  https://github.com/vfi64/agentic-project-kit/blob/main/docs/reports/POST_V1_0_7_B1_COMM_SCI_CYCLE_006_MERGE_WRAPPER_RETEST_20260829.md

## Claims Deliberately Avoided

- General brownfield portability is not claimed.
- The command count is not used as a quality metric.
- The project history PR count is not used as quality evidence.
- Remote CI success is not claimed for cycles where the target repository
  reported no checks.
- Fixes on main and fixes in a released package are kept as separate evidence
  types.
- The GUI is not presented as full CLI parity.
