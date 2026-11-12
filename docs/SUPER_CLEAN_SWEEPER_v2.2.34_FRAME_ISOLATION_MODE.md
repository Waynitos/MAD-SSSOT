# v2.2.34 — Frame Generator Isolation Mode (proposed workaround)

## User idea
When GA recursion encounters a Frame Generator subassembly, open and process that frame independently, then return to recursive processing of the remaining GA items. Treat as a potential workaround for save-context errors, **not a proven fix**.

## Design
- **Indexer:** detect frame candidates from supported Inventor evidence; capture skeleton, generated members, parent occurrence paths and document identities. Never classify solely from filenames.
- **Copy Planner:** create a unique frame-isolation work item keyed by verified source/target identity; schedule its dependencies before parent assembly replacement. Handle nested frames and shared occurrences; avoid cycles and duplicate processing.
- **Executor:** at a controlled safe point, open the **target** frame as an independent document, verify its skeleton/member references, perform approved update/repair and save in tested context, then close/release it safely. Do not recursively invoke the whole Clean Sweeper rule from within itself.
- **Resume:** revalidate the saved target frame and parent reference mappings, then replace it in the parent and continue GA traversal. Parent and GA save remain separate guarded operations.
- **Failure:** fail closed; leave parent unmodified or journal precisely what changed. Never treat a successful independent frame save as proof that GA-level save will work.

## Inventor context cautions
- Opening the same frame separately while GA already has it loaded may not provide truly independent document state; design experiments for GA-open vs GA-closed, separate Inventor session if necessary.
- A Frame Generator skeleton may require parent frame assembly context; opening the frame alone may or may not resolve it.
- Preflight Vault checkout, file write permissions, dirty states, missing/external refs and active project. Do not force refresh, close unsaved documents, or silently save checked-in files.
- Avoid stale in-memory GA references: reload/re-resolve and read back the dependency graph after isolation work.

## Diagnostic A/B tests
Compare (1) repair/save from GA context, (2) opening frame directly with GA still open, (3) opening frame from a clean Inventor session, using independent disposable copies of the same baseline frame. Log API errors, save prompts, document identities, dirty flags, graph diffs and timings to SQLite.

## Acceptance
- Frame remains editable/associative and all skeleton/member references point to intended targets.
- No unexpected prompts, source project mutation or duplicated copy work.
- Parent/GA can subsequently be saved and reopened with correct references.
- Any failure produces a recoverable journal and actionable diagnostics.

Status: research/design only; no implementation or Inventor runtime verification claimed. Feature branch only, no production/main changes.
