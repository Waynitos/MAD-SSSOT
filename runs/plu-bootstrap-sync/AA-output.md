# AA Output — PLU Sync Architecture
MAD Run: plu-bootstrap-sync | Date: 2026-10-25

## Position defended
The GitHub-fetch architecture is fundamentally sound. The pasted instruction block is the correct bootstrap layer — it just needs a compact trigger glossary added so Claude knows RMAD/Mini-MAD before any network fetch completes.

## Argument
The GitHub-fetch architecture is not 90% solved — it IS solved, by design. Every session in every project starts by fetching a fresh copy of PROJECT-LAUNCH-Plus.md. Any update to MAD routing rules, branding tokens, FTCA protocols, or trigger-word definitions propagates universally on the next session open, with zero per-project action. This is textbook SSSOT: one file, one truth, infinite consumers.

The trigger-word amnesia problem is real but surgically small. It only fires when Claude reads a trigger word *before* the PLU fetch completes — i.e., in the user's opening message. The fix does not require redesigning the architecture; it requires adding ~8 lines to the instruction block. The instruction block is the only thing guaranteed to be present before the fetch.

Embedding a compact glossary in the instruction block is the correct layering. The instruction block bootstraps Claude's context before any external fetch. Trigger-word definitions are bootstrap-level knowledge. PLU-on-GitHub is the right place for full protocol detail and evolution. The instruction block is the right place for zero-latency, always-available primer.

## Strongest evidence
- PLU.md is fetched at START of every session — propagation lag is zero sessions
- Instruction block text has not needed changing since v1.0 despite PLU evolving through v1.4
- Trigger-word amnesia only fires in one edge case: user's first message contains RMAD before PLU loads
- Glossary fix requires ~8 lines added to one template file (PLU-wizard.md Step 4)

## Proposed fix
Add trigger glossary to instruction block template. RMAD, Mini-MAD, FTCA, PLU, SSSOT defined before any fetch.
