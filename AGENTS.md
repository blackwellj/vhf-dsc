# VHF-DSC Agent Guide

## Project Boundary

This is the independent DSC encoder/decoder repository at `/root/DSC/vhf-dsc`. Treat it as a separate implementation from `/root/coastalhub/apps/vhf-dsc-decoder`. Understand and test each implementation independently before comparing them.

## Mandatory AI Efficiency and Value Rules

1. **Inspect directly first.** Use deterministic file, Git, test, DSP-analysis, and benchmark commands before invoking another LLM.
2. **One outcome per coding session.** Start a fresh agent session for each investigation, encoder/decoder change, benchmark, or review. Do not reuse long or unrelated sessions.
3. **Scope before execution.** State the goal, files/modules, exclusions, acceptance criteria, verification, and budget class before coding.
4. **Load context on demand.** Do not preload the complete ITU documents, audit report, captured-audio corpus, or every source file. Read the exact standard sections and samples required for the current task.
5. **Use the cheapest adequate method.** Direct tools first; inexpensive models for exploration and routine implementation; stronger models only for difficult DSP/protocol reasoning. Max-tier models require justification and a fresh, short session.
6. **Control delegation.** One exploration subagent by default. Do not run overlapping whole-project audits. A second agent is appropriate only for independent validation or diff review.
7. **Default spend targets.** Small fix: $0.50; normal feature: $2; large investigation/refactor: $5. Pause and report before materially exceeding the target unless a larger budget was approved.
8. **Protect evidence and current work.** Check `git status` before edits. Preserve unrelated changes. Never modify or delete captured audio, reference documents, expected outputs, or benchmark evidence as part of making tests pass.
9. **Verify objectively.** Run targeted unit tests, then relevant integration and corpus tests. For decoder comparisons, use the same labelled corpus and report decode rate, false positives, field accuracy, timing/frequency tolerance, CPU/memory, and latency.
10. **No favourable-result tuning.** Do not tune one implementation on the evaluation set and then call the comparison fair. Separate development and holdout samples where practical.
11. **Finish with evidence.** Report files changed, exact tests/commands and results, remaining risks, and approximate LLM usage. Do not claim completion without real execution.
12. **Store knowledge, not giant conversations.** Capture stable architecture, protocol assumptions, benchmark definitions, and decisions in concise documentation, then end the task session.

## Default Task Brief

Before implementation, establish: **Goal · Scope · Do not touch · Acceptance criteria · Verification · Budget class**.

## Mandatory Git Hygiene

1. At the start of every task run `git status --short`, identify the branch/upstream, and `git fetch --all --prune`. Report dirty, ahead, behind, and diverged states before editing.
2. If the working tree is clean and the branch is only behind, update with fast-forward only (`git pull --ff-only`). Never merge or rebase implicitly.
3. If the branch has local commits and remote commits, or unrelated working-tree changes, stop and present a reconciliation plan. Do not stash, reset, rebase, merge, or force-push without an explicit preservation strategy.
4. Preserve unrelated changes. Stage explicit paths, review `git diff --cached`, and make focused commits tied to one verified outcome. Never use blanket `git add -A` in a dirty repository.
5. Never commit secrets, credentials, captured audio, logs, databases, runtime state, generated outputs, or caches unless explicitly designated as test fixtures.
6. After tests pass, report the proposed commit and push scope. Push normal focused commits to the configured upstream; obtain explicit approval before publishing a large backlog or resolving/re-writing divergent history.
7. Never force-push a protected/shared branch. Create a backup branch before non-fast-forward reconciliation.
8. End every task by reporting branch, commit SHA (if created), upstream sync state, push result, and remaining working-tree changes.

## Comparison Rule

Do not replace or merge either DSC implementation based on subjective code review alone. Any recommendation must be supported by reproducible tests against a shared corpus and clearly stated operational constraints.