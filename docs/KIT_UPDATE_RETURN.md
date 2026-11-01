# Governed return after Kit adoption

KIT-GF-095 provides a bounded return to the prior pinned Kit 1.1.10. It does not
enable general downgrades. Normal `kit update --version` and `--latest` retain
their downgrade prohibition. Start from the immutable adoption receipt and its
observed PR number in `.agentic/kit-update`; never find the PR by commit subject.

1. On a normal Kit work branch, plan `agentic-kit kit return-revert --adoption
   <receipt-id> --json`. It observes the exact merged adoption PR, requires a
   single-parent squash commit, verifies its exact paths and before/after hashes,
   rejects later commits touching those paths, and reverse-applies the diff in
   check-only mode. BLOCKED preserves all files and evidence.
2. Review the signed plan and execute the same route with `--execute
   --expected-signature <signature>`. It restores the adoption files byte for
   byte while preserving later unrelated work. Use normal Kit work finish,
   commit, push and PR routes. Their PR observation binds the actual return PR.
   Merge remains owner-controlled. A verified return does not regenerate v2.
3. After the return PR is merged, closeout remains PENDING. New Kit validation
   correctly reports `NEEDS_PROJECTION_MIGRATION`; it must not silently accept
   restored v1. Plan `agentic-kit kit return-install --adoption <receipt-id>
   --json`. This requires restored v1, no handoff minimum key, both pins exactly
   1.1.10, verified merged return PR and an empty target `changed_paths`.
4. The owner approves the exact signed installation plan using the same route
   with `--execute --expected-signature <signature>`. This reuses the existing
   two-phase updater: index and SHA256-verified staged wheels, repeated
   preconditions under lock, separate offline pip process, and fresh-process
   target `check` and `doctor`. Both checks must pass under the actual installed
   target. Empty paths alone prove no compatibility.
5. Continue normal post-merge verification and chat switch under 1.1.10. Failed
   installation or final checks yield BLOCKED/INCOMPLETE, retain completed-step
   progress and append audit evidence. Diagnose before retrying; do not repair
   files manually or discard failure evidence.

The local machine test uses an installation test double. Before release, an
external desktop controller must repeat the complete adoption, revert,
installation return, `check`, `doctor`, `post-merge-check` and v1 chat switch in a
disposable copy using real wheels. A release containing KIT-GF-094 requires this
rehearsal PASS, local return PASS and owner acceptance of both. Historical
approvals and ledger entries are never rewritten.
