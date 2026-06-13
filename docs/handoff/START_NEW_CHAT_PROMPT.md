---
schema_version: 2
artifact_type: chat_switch_prompt
role: start_new_chat
canonical_bootstrap: docs/handoff/NEXT_CHAT_BOOTSTRAP.md
successor_context: docs/reports/handoff-packages/latest/successor_context.yaml
paired_prompt: docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
must_update_together:
  - docs/handoff/START_NEW_CHAT_PROMPT.md
  - docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
  - docs/handoff/NEXT_CHAT_BOOTSTRAP.md
required_terms:
  - successor_context.yaml
  - source_manifest.json
  - validation_report.json
  - agentic-kit transfer chat-switch-complete
  - AGENTS.md
  - README.md
  - SECURITY.md
  - FINAL_SUMMARY_CONTRACT.md
  - handoff_state.yaml
  - compiled_agent_context.yaml
  - Rule Registry
  - boot write
  - PASS_ALREADY_DONE
  - d/f
  - red CI
---

# Start New Chat Prompt

Copy `docs/reports/handoff-packages/latest/successor_prompt.md` into the successor chat.

The successor chat must treat the Successor Handoff Package as the short-term handoff and the repository files listed in `source_manifest.json` as long-term truth.

If the package validation is not PASS, or if HEAD/local status differs from the package without explanation, stop and repair handoff drift first.
## Operational documentation refresh state after PR #1272

Current administrative handoff refresh state is `58f1fe76` (`Refresh successor handoff after PR1271 (#1272)`). Continue next only after this post-PR1272 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1273

Current administrative handoff refresh state is `509d4119` (`Refresh successor handoff after PR1272 (#1273)`). Continue next only after this post-PR1273 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1274

Current administrative handoff refresh state is `4d536e2c` (`Refresh successor handoff after PR1273 (#1274)`). Continue next only after this post-PR1274 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1275

Current administrative handoff refresh state is `f56fee9b` (`Refresh successor handoff after PR1274 (#1275)`). Continue next only after this post-PR1275 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1276

Current administrative handoff refresh state is `22e1e13d` (`Refresh successor handoff after PR1275 (#1276)`). Continue next only after this post-PR1276 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1277

Current administrative handoff refresh state is `e3d5cf4a` (`Refresh successor handoff after PR1276 (#1277)`). Continue next only after this post-PR1277 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1278

Current administrative handoff refresh state is `de4f1bc7` (`Refresh successor handoff after PR1277 (#1278)`). Continue next only after this post-PR1278 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1279

Current administrative handoff refresh state is `79795ae3` (`Refresh successor handoff after PR1278 (#1279)`). Continue next only after this post-PR1279 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1281

Current administrative handoff refresh state is `dfb22003` (`Skip admin refresh for refresh-only PRs (#1281)`). Continue next only after this post-PR1281 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1283

Current administrative handoff refresh state is `60765225` (`Treat refresh-only post-merge state as fresh (#1283)`). Continue next only after this post-PR1283 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1285

Current administrative handoff refresh state is `9db86a0c` (`Add successor execution contract projection (#1285)`). Continue next only after this post-PR1285 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1287

Current administrative handoff refresh state is `efe9d176` (`Write successor execution contract file (#1287)`). Continue next only after this post-PR1287 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1289

Current administrative handoff refresh state is `1214bc04` (`Harden successor execution contract validation (#1289)`). Continue next only after this post-PR1289 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1291

Current administrative handoff refresh state is `d6ec1947` (`Report refresh-only post-merge status as noop (#1291)`). Continue next only after this post-PR1291 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1293

Current administrative handoff refresh state is `7516fb3a` (`Update outer docs for successor handoff package (#1293)`). Continue next only after this post-PR1293 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1295

Current administrative handoff refresh state is `d2c844be` (`Add E2E successor handoff contract test (#1295)`). Continue next only after this post-PR1295 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1297

Current administrative handoff refresh state is `3a3368fd` (`Close out documentation system handoff pointers (#1297)`). Continue next only after this post-PR1297 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1299

Current administrative handoff refresh state is `882b43b3` (`Polish command reference and clean repo status (#1299)`). Continue next only after this post-PR1299 refresh is committed and merged; the next substantive slice must be created from fresh main.

## Operational documentation refresh state after PR #1301

Current administrative handoff refresh state is `3cf3090b` (`Close out documentation system hardening (#1301)`). Continue next only after this post-PR1301 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1303

Current administrative handoff refresh state is `794ceff0` (`Fix operational handoff refresh newlines (#1303)`). Continue next only after this post-PR1303 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1305

Current administrative handoff refresh state is `b7a917e7` (`Harden successor bootstrap acceptance gate (#1305)`). Continue next only after this post-PR1305 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1307

Current administrative handoff refresh state is `e88a5591` (`Harden successor package freshness gates (#1307)`). Continue next only after this post-PR1307 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1309

Current administrative handoff refresh state is `e9371b44` (`Protect start prompt during successor package refresh (#1309)`). Continue next only after this post-PR1309 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1311

Current administrative handoff refresh state is `afc21ade` (`Project bootstrap gate into successor package (#1311)`). Continue next only after this post-PR1311 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1314

Current administrative handoff refresh state is `e8f02f20` (`Accept refresh-only successor package head drift (#1314)`). Continue next only after this post-PR1314 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1317

Current administrative handoff refresh state is `23c913f9` (`Refresh successor package after PR1316 (#1317)`). Continue next only after this post-PR1317 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1320

Current administrative handoff refresh state is `879b6f89` (`Harden admin refresh PR freshness check (#1320)`). Continue next only after this post-PR1320 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1324

Current administrative handoff refresh state is `75d7a3d3` (`Refresh successor package during admin handoff refresh (#1324)`). Continue next only after this post-PR1324 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1326

Current administrative handoff refresh state is `967d7380` (`Refresh successor package during admin handoff refresh (#1326)`). Continue next only after this post-PR1326 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1330

Current administrative handoff refresh state is `a7a0b6a2` (`Audit ns to agentic-kit migration before GUI (#1330)`). Continue next only after this post-PR1330 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1332

Current administrative handoff refresh state is `d3685e2a` (`Plan ns to agentic-kit migration before GUI (#1332)`). Continue next only after this post-PR1332 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1334

Current administrative handoff refresh state is `c6ab40da` (`Classify ns migration docs before GUI (#1334)`). Continue next only after this post-PR1334 refresh is committed and merged; the next substantive slice must be created from fresh main.
