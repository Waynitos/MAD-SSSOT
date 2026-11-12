# PWTP — Pow Wow Transit Process
## SUPER CLEAN SWEEPER experimental development protocol

**Status:** Adopt as working development approach for the v2.2.34 feature branch; this document does not claim tests have run or code has been validated in Inventor.

### Purpose
Replace long speculative release cycles with short, evidence-driven, runnable experiments. Each experiment can redirect the architecture before the full rule is changed. Preserve production/main and v2.2.33 profiler baseline.

### Cycle
1. **Pow Wow:** articulate a single falsifiable hypothesis and competing explanations.
2. **Isolate:** build the smallest disposable model/rule that tests it, with defined baseline.
3. **Test:** run in Inventor 2025; capture exact input, context, logs, prompts, and output.
4. **Diagnose:** compare expected/observed behaviour, successes/failures and counterexamples.
5. **Transit:** adopt, revise, abandon, or split the approach; update subsequent sprint priorities and architectural assumptions.

### Sprint contract
Each PWTP sprint must specify: ID, hypothesis, controlled input model, test rule location, run instructions, safe defaults, expected outcome, actual outcome, raw log paths, API errors, limitations, pass/fail/inconclusive, decision, next experiment, and promotion criteria. **No unexecuted test may be called passed.**

### Initial backlog
- PWTP-01: read-only reference graph/identity diagnostic for frame, parent, GA. Existing experimental rule: `scripts/ilogic/experiments/FRAME_CONTEXT_DIAGNOSTIC_READONLY.iLogicVb`. This has been committed but **not compiled or run in Inventor**.
- PWTP-02: controlled independent frame copy/update/save on disposable baseline.
- PWTP-03: same-frame parent/GA context comparison, restored baseline per test.
- PWTP-04: standard subs first, deferred frames second, reconciliation third.
- PWTP-05: frame skeleton/member associativity and parent reconnect validation.
- PWTP-06: SQLite read-only snapshots, graph diffs, identity/provenance checks.
- PWTP-07: integrate only demonstrated behaviours into existing Indexer / Copy Planner / Executor and run regression checks.

### Guardrails
- No changes to production, Vault-managed source models or main branch.
- Read-only first; explicit user-controlled opt-in for save/copy tests on disposable files.
- Revalidate Inventor/Vault live state before any mutation; SQLite is observation/plan store.
- Preserve failed approaches and their logs to prevent repeating mistakes.
- Do not assume a successful copy means the frame and GA save correctly.
- Do not wait for a polished release before seeking user-run Inventor evidence.

### Decision record template
`PWTP-ID | hypothesis | test model | active context | result | evidence/log | decision (adopt/revise/reject/inconclusive) | impact on architecture | next test`
