# Vault Cloud Migration — MAD Run

**Status:** AA and DA briefs ready. SSA pending DA output.  
**Initiated:** October 2026  
**Topic type:** Enterprise Software Adoption  
**Live case study:** Yes — active migration in progress at design department

## How to Run This

1. **AA Agent** — open a fresh AI session, paste `AA-brief.md`, let it build the full case for migration
2. **DA Agent** — open a separate fresh AI session (do NOT use the same session as AA), paste `DA-brief.md`, let it challenge every angle
3. **SSA Agent** — open a third fresh session, paste both AA and DA outputs plus the SSA prompt from `prompts/ssa-prompt.md`, synthesise the final recommendation

## Critical Priority

The **Plant 3D / Vault integration** is the highest-risk item in this migration. It must be in the first round of test cases — not an afterthought. See DA brief for the specific failure modes and test requirements.

## Files

- `AA-brief.md` — Advocate Agent brief (build the case for migration)
- `DA-brief.md` — Devil's Advocate brief (find every way it can fail)
- `SSA-output.md` — to be created after DA run completes

## What Makes This Case Study Valuable

This is a real migration with real stakes. The DA brief captures:
- A known, documented failure mode (Plant 3D check-in/check-out direction)  
- Latency implications of cloud vs LAN for CAD file operations
- File relationship integrity risks during migration
- Questions to stress-test the adequacy of the test cases provided by IT
- Rollback readiness assessment

The MAD output from this run should be presented to management **before** go-live approval is given.
