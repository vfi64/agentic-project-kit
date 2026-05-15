diff --git a/AGENTS.md b/AGENTS.md
index 2910d25..ea30da0 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -123,7 +123,7 @@ Use Architecture Decision Records (ADRs) for durable architecture choices with r
 
 These governed workflow principles are currently review-only unless a specific feature turns them into deterministic tests, schema checks, doctor checks, documentation coverage, or CLI contracts. Reviewers should inspect whether a design reduces drift, improves restartability, preserves evidence, and keeps simple workflows simple.
 
-See `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md` for preserved workflow-pattern notes and `docs/ideas/LAYERED_CLI_USABILITY.md` for the non-binding usability-layer model that keeps the CLI Golden Path small while allowing advanced automation.
+See `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md` for preserved workflow-pattern notes, `docs/ideas/LAYERED_CLI_USABILITY.md` for the non-binding usability-layer model that keeps the CLI Golden Path small while allowing advanced automation, and `docs/ideas/DIDACTIC_GUIDANCE.md` for the non-binding orientation layer that keeps state, handoffs, gates, and safe next steps understandable.
 
 ## Remote Work Authorization
 
diff --git a/docs/STATUS.md b/docs/STATUS.md
index 2ca19a8..f048f7a 100644
--- a/docs/STATUS.md
+++ b/docs/STATUS.md
@@ -79,6 +79,8 @@ Layered CLI Usability is a review lens for keeping the public command surface ma
 
 Pattern Advisor remains optional and advisory. It preserves the idea of mapping recurring project evidence to reusable patterns, anti-patterns, and candidate patterns without becoming an autopilot, a gate, or a wrapper-specific subsystem.
 
+Didactic guidance is documented in `docs/ideas/DIDACTIC_GUIDANCE.md` as a non-binding orientation layer for making project state, handoffs, gates, and safe next steps easier to understand without adding runtime behavior, gates, or automatic decisions.
+
 No ADR has been created for these idea notes. An ADR should be considered only when DCO, layered CLI usability, Pattern Advisor behavior, capability boundaries, or a guided CLI entry point become binding architecture or public CLI policy.
 
 ## Documentation-mesh audit state
diff --git a/docs/handoff/CURRENT_HANDOFF.md b/docs/handoff/CURRENT_HANDOFF.md
index b90dd22..aa1e3cc 100644
--- a/docs/handoff/CURRENT_HANDOFF.md
+++ b/docs/handoff/CURRENT_HANDOFF.md
@@ -131,6 +131,7 @@ The project should continue to emphasize:
 - a clear semantic quality boundary: deterministic gates can check structure and drift, but human review owns semantic correctness unless a property is converted into a deterministic rule;
 - CLI usability discipline so growing automation does not make daily use harder;
 - advisory pattern work as optional support, not as a replacement for maintainer judgment.
+- didactic guidance as a non-binding orientation layer documented in `docs/ideas/DIDACTIC_GUIDANCE.md`, separate from runtime behavior, deterministic gates, and Pattern Advisor implementation.
 
 ## Source of Truth
 
diff --git a/docs/ideas/DIDACTIC_GUIDANCE.md b/docs/ideas/DIDACTIC_GUIDANCE.md
new file mode 100644
index 0000000..877c4e0
--- /dev/null
+++ b/docs/ideas/DIDACTIC_GUIDANCE.md
@@ -0,0 +1,50 @@
+# Didactic Guidance
+
+Review policy: keep while didactic guidance is an active architecture option
+Next review: before adding public advisory review commands or before v0.4.0
+
+## Purpose
+
+This note documents didactic guidance as a non-binding orientation layer for `agentic-project-kit`.
+
+The kit is not only a command collection. It is also a method for making agentic project work understandable, restartable, teachable, and auditable.
+
+Didactic guidance explains how project state, handoffs, gates, workflow requests, and idea notes help humans and agents understand what is happening, why it is happening, and what a safe next step looks like.
+
+## Contract
+
+Didactic guidance is advisory, human-facing, and documentation-first.
+
+This foundation slice must not add runtime code, public CLI commands, deterministic gates, workflow states, Pattern Advisor implementation, or pattern catalog behavior.
+
+## Guidance questions
+
+Didactic guidance should help a maintainer or agent answer five questions:
+
+1. What is the current state?
+2. What is the intended next step?
+3. Which rules are binding and which are advisory?
+4. What must not be mixed into this slice?
+5. What evidence is needed to trust the result?
+
+## Relation to deterministic gates
+
+`doctor`, `check-docs`, and `doc-mesh-audit` are hard checks for known structural and consistency problems.
+
+They cannot prove didactic optimality, audience fit, architectural wisdom, or future handoff sufficiency.
+
+Any future didactic review command must remain advisory unless it is converted into a deterministic rule with a clear, testable failure condition.
+
+## Relation to Pattern Advisor
+
+Pattern Advisor work remains separate.
+
+Didactic guidance can make Pattern Advisor safer later by clarifying how advice should be framed, limited, and explained.
+
+This note does not approve a Pattern Advisor MVP, a pattern catalog, automatic suggestions, candidate capture, promotion or deprecation workflow, or public `patterns` / `advise` CLI behavior.
+
+## Current decision
+
+For now, didactic guidance is documented as an idea-level orientation layer.
+
+It is advisory, human-facing, documentation-first, and separate from deterministic gates and runtime behavior.
diff --git a/docs/reports/didactic_guidance_inspection.md b/docs/reports/didactic_guidance_inspection.md
new file mode 100644
index 0000000..9878442
--- /dev/null
+++ b/docs/reports/didactic_guidance_inspection.md
@@ -0,0 +1,22 @@
+# Didactic guidance slice inspection
+
+## Branch
+
+docs/didactic-guidance-foundation
+
+## Status
+
+?? docs/reports/didactic_guidance_inspection.md
+
+## Didactic guidance file
+
+DIDACTIC_GUIDANCE_MISSING
+
+## Candidate link locations
+
+docs/STATUS.md:80:Pattern Advisor remains optional and advisory. It preserves the idea of mapping recurring project evidence to reusable patterns, anti-patterns, and candidate patterns without becoming an autopilot, a gate, or a wrapper-specific subsystem.
+docs/STATUS.md:152:Future Pattern Advisor architecture track:
+docs/STATUS.md:237:Start the next concrete slice only after defining a one-paragraph user-facing goal and an explicit command-level contract. Keep Pattern Advisor non-binding unless separately approved.
+docs/TEST_GATES.md:122:Advisory review may later evaluate clarity, didactic quality, audience fit, missing rationale, and possible architecture drift. Such advisory review must remain separate from hard gates unless it is converted into a deterministic rule with a clear failure condition.
+README.md:167:Future commands such as `review-docs` or `review-architecture` may provide advisory review for clarity, didactic quality, audience fit, missing rationale, overclaims, architecture drift, or review questions. Such advisory review must remain separate from `doctor` and must not be treated as merge authority.
+AGENTS.md:126:See `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md` for preserved workflow-pattern notes and `docs/ideas/LAYERED_CLI_USABILITY.md` for the non-binding usability-layer model that keeps the CLI Golden Path small while allowing advanced automation.
