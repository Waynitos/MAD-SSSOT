# SSA Output — PLU Sync Architecture
MAD Run: plu-bootstrap-sync | Date: 2026-10-25

## Verdict table

| Question | AA | DA | SSA verdict |
|---|---|---|---|
| Is architecture sound? | Yes, SSSOT works | Only for PLU content — block is static | Partially — content layer works, bootstrap layer fragile |
| Trigger-word fix? | Add glossary to block | Block should be minimal | DA wins — glossary in bootstrap FILE, not in pasted block |
| Block evolution problem? | Block rarely changes | Can't push changes to existing projects | DA wins — shrink block to one URL |
| Sub-file misses? | On-demand is fine | Silent gaps when new files added | DA wins — bootstrap defines required auto-fetches |

## Decision: PLU-bootstrap.md pattern adopted

**The instruction block is now one line:**
```
At session start, fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-bootstrap.md and follow every step in it exactly.
```

**PLU-bootstrap.md (new file, lives on GitHub) owns:**
- Trigger word glossary (RMAD, Mini-MAD, FTCA, PLU, SSSOT, AA, DA, SSA) — parsed before any fetch
- Ordered fetch sequence (PLU → PROJECT-CONFIG → branding → wizard check → FTCA)
- Fallback rules if fetch fails
- Version check logic

**What this solves:**
- ✓ Trigger word amnesia — glossary is in bootstrap, fetched in first line of every session
- ✓ Instruction block drift — block is now one URL, never changes
- ✓ Sub-file misses — bootstrap explicitly lists all required fetches in order
- ✓ Future-proofing — all logic evolution happens in GitHub, zero per-project re-paste
- ✓ Fetch failure — bootstrap has a fallback block with minimum viable rules inline

**What it cannot solve:**
- ✗ If the bootstrap URL itself changes (repo rename, etc.) — but this is far less likely than logic changes
- ✗ Existing projects with old instruction block pasted — they need one-time re-paste of the new single line

## Win-wins
- Old instruction block was ~180 words. New one is 14 words. Easier to paste, easier to verify, easier to audit.
- Bootstrap file can evolve freely on GitHub — add new trigger words, new fetch steps, new fallback rules — without touching any project
- The "one manual action" story to users is now cleaner: "paste one line, done forever"

## Implementation completed
- PLU-bootstrap.md created in MAD-SSSOT repo
- PLU-wizard.md Step 4 updated to generate new single-line instruction block
- PLU-wizard.md Step 5 (PLU-missing guard) updated with new single-line block
- PROJECT-LAUNCH-Plus.md bumped to v1.5 with changelog entry
