# DA — Devil’s Advocate: Strongest Case AGAINST further code changes

**Topic:** Ensuring Phase 2 of the two-phase Clean Sweep rule always updates and saves all drawings after models have been renamed.

## Strongest Case AGAINST

The models are already 100 % renamed and saved. The only reason drawings did not save was a single unguarded COM member access. Adding more fallbacks and re-run logic increases complexity without addressing the fundamental Inventor constraints that have caused every previous round of “almost there” failures.

1. **COM surface is incomplete and version-dependent** — `RevisionTags` is only one example. Other members (`RevisionClouds` on some releases, certain `DrawingView` properties, OLE descriptors) can throw the same “Public member not found” error. A Try/Catch on one property does not make the drawing pass robust; it merely moves the next crash further down the function. The real limit is Inventor’s late-bound interop, not missing Try/Catch blocks.

2. **Re-run fallback hides design debt** — Reconstructing paths from `oNameOverrides` on a second run papers over the fact that the first run aborted. If the first run had succeeded, the fallback would never be needed. Investing in re-run paths encourages a workflow of “run, crash, fix, re-run” instead of a single reliable pass.

3. **Frame_ skip is a symptom** — Skipping `\Frame_` folders avoids noise but does not fix the underlying Frame Generator isolation problems that have required multiple special-case paths (file-copy + ReplaceReference, isolated open, deferred processing). Those problems remain.

4. **Memory and Vault interaction remain unsolved** — Even with `Update2(True)` and `DeferUpdates = False`, large drawing sets have previously exhausted memory when source files stayed open. The current CloseAll(False) pattern helps, but it is still a work-around for Inventor’s document lifetime model. Further code changes will not change that.

The correct next step is to accept the v1.0.4 Try/Catch as the minimal patch, re-run Phase 2 once, and stop. Additional architectural work (SQLite control plane, separate Inventor session, etc.) should be evaluated only after the drawings are confirmed saved, not before.
