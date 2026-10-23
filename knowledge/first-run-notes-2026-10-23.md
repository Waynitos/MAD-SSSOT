# First MAD Run Notes — 2026-10-23

**Topic:** MAD-SSSOT system self-evaluation
**Run by:** Claude (claude-sonnet-4-6), MAD PROJECT session
**Mode:** Single-model sequential (AA → DA → SSA in one context window)

## What worked
- Role separation was clean and held throughout
- DA surfaced three genuine gaps not in the AA case:
  - Single-model anchoring limitation (now filed as failure mode)
  - Missing `prompts/SA.md` file (referenced in LAUNCH.md but absent)
  - Empty `knowledge/` folder — the living knowledge base had no content
- SSA executive summary was actionable
- Repo was fully AI-readable from a cold start via LAUNCH.md

## What to fix (priority order)
1. Add `prompts/SA.md` — LAUNCH.md references it but it doesn't exist
2. Populate `knowledge/` — this run is the first entry
3. Create one example completed run in `runs/` for pattern reference
4. Add domain-threshold table to DA prompt (staleness thresholds by topic type)
5. Add a note to LAUNCH.md acknowledging single-model anchoring limitation

## Token / context notes
Full AA → DA → SSA cycle on a moderate topic fits comfortably in one session.
For complex topics, SSA synthesis may need to be run in a fresh context with
AA and DA outputs pasted in.

## Next run suggestion
Run a real-world topic (e.g. the Even Realities G2 test suggested in
MAD_Agent_Prompts.md) to validate against a known subject with findable
ground truth.
