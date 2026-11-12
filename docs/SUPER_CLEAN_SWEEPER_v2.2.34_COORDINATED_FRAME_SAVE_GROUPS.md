# v2.2.34 — Lower-level replacement succeeds, Frame Generator skeleton blocks save

## User's observed reproduction
During SUPER CLEAN SWEEPER reruns repairing lower-level subassemblies that the initial GA / GA Drawing copy did not fix, the old subassembly references are successfully swapped for new target copies. **Only when saving afterward**, Inventor opens a save dialog resembling the one encountered for a checked-in subassembly. The Frame Generator skeleton is implicated, **but the user believes this skeleton is not checked in**. Do not equate this prompt with proven Vault checkout failure.

## Working hypothesis
The replacement phase succeeds but leaves an interdependent Frame Generator skeleton/frame/member/parent document set dirty or requiring a specific assembly save context. Independent copy/replace/save ordering may be invalid. A **dependency-aware coordinated save group** may be needed; it is not yet proven that one API save call or a fixed bottom-up order works.

## Required diagnostics
1. Capture exact Inventor save-dialog text, full document paths, modified/dirty state, save-required flags, read-only and Vault checkout/ownership states for each affected file; capture before replacement, after replacement, before save, and after save attempt.
2. Record full parent-child reference edges and original/target paths for skeleton, driving sketch, generated frame members, frame subassembly, enclosing lower-level subs, GA, GA drawing and related IPNs.
3. Determine which document's edit causes skeleton dirtying, and whether opening/activating the parent frame changes save behavior.
4. Compare controlled save orders and contexts on disposable copies: skeleton/frame group first; parent-first; explicit update then save; Save2/SaveAs semantics where supported. Never assume all Frame Generator files must be saved together or that bottom-up ordering is always safe.
5. Preflight every file in the proposed group for Vault ownership, read-only, write permissions, external references, existing targets and changes since preview.
6. If any member fails preflight or save, block group completion, journal affected documents, and preserve recoverable original state. Avoid silently saving unrelated or checked-in documents.
7. Preserve v2.2.33 profiler checkpoints and log time spent in graph discovery, reference replacement, dirty-state propagation, save preflight, save operations and readback verification.

## Proposed design
Introduce **Frame Generator coordinated save groups** as a planning and diagnostic abstraction. Treat a group as a strongly related set of documents that must be validated together, not as a guaranteed atomic Inventor transaction. Repair sequencing must be derived from actual dependency edges, with reverse references verified before considering success. Independent drawing-only models remain late in the repair order after GA graph integrity.

## Acceptance case
Reproduce an initially incomplete GA/GA Drawing sweep, rerun to replace an old nested subassembly successfully, then verify that its frame skeleton and associated documents can be saved without unexpected prompts, without old-project links, without violating Vault permissions, and without damaging editability of generated members. No Inventor execution validation claimed.
