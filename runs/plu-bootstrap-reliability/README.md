# RMAD Run: plu-bootstrap-reliability
Date: 2026-10-25
Topic: External URL fetch bootstrap architecture — reliability and safety training conflict
Triggered by: Waynito (phewphonics@hotmail.com)

## SSA Verdict (short form)
**DA wins on mechanism. AA wins on principle. Hybrid architecture resolves both.**

- Bootstrap fetch is structurally blocked by Claude's safety training (prompt injection heuristic)
- Inconsistent execution (sometimes fetches, sometimes refuses) confirmed in live testing
- Trigger definitions move INLINE into project instructions — stable, trusted, always present
- GitHub remains SSSOT for content fetched on user-directed triggers (PHONICSPlus, FTCA, wizard, run outputs)
- NEWPROJECT trigger updated to output full inline block, not a URL

## Files
- `AA-output.md` — Preserve fetch architecture; single-update propagation is the core value
- `DA-output.md` — Abandon fetch; safety training makes it structurally unreliable
- `SSA-output.md` — Full verdict, hybrid architecture, tool matrix, immediate actions

## Winner
DA on bootstrap mechanism. AA on SSSOT principle. Hybrid design preserves both.
