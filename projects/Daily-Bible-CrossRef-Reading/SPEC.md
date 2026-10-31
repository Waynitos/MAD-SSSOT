# Daily Bible Cross-Reference Reading Project — Spec
_Last updated: 2026-10-31_

This document is the authoritative spec for the Daily Bible Cross-Reference Reading Project.
Any session working on this project must read this before making changes.

Source of architectural decisions: SSA from RMAD in runs/Daily-Bible-CrossRef-Reading-Project/

---

## Entry point

- Phase 1: Claude Project (custom instructions + conversation or memory for progress).
- User opens the Project and requests “today’s reading” or “next day”.
- Optional: scheduled Automation that posts the day’s set.
- Later phases: simple web flashcard UI or app.

## Step-by-step flow

1. Determine current day index (start: day 1 = Genesis 1). Persist in Project memory or user state.
2. Load the OT chapter for the day (sequential from Genesis 1 onward).
3. Select one high-signal linked passage from each category using priority:
   - Direct quotation or clear allusion (highest).
   - Strong thematic match from TSK / CrossReferences-org data.
   - Documented fallback with note that it is thematic.
   Prefer unused references across days where possible.
4. Present as four sequential flashcards:
   - Card 1: OT chapter (or selected key verses if very long; full chapter preferred when practical).
   - Card 2: Psalms or Proverbs.
   - Card 3: Gospels.
   - Card 4: Letters to churches or Revelation.
5. Each card shows: KJV text, reference, optional one-line connection note.
6. Controls: “Next” advances to next card or (after last) offers next day / menu. Persistent “Menu” button.
7. Menu options:
   - Continue next day (advances day index).
   - Custom topic (free-text entry).
   - (Later) View progress.
8. Topic mode flow:
   - User enters topic (e.g. “God’s Joy”).
   - Return first/strongest mention in OT, then Ps/Prov, then Gospels, then Epistles/Rev, each with selection note.
   - Present as flashcards; option to return to daily mode.

## Key variable notes

| Variable | What it is | Set where |
|---|---|---|
| day_index | Integer starting at 1 (maps to OT chapter sequence) | Project memory / user state / Automation |
| ot_chapter | Current OT book + chapter (e.g. Genesis 1) | Derived from day_index |
| selected_ps | Chosen Ps/Prov reference for the day | Selection logic |
| selected_gospel | Chosen Gospel reference | Selection logic |
| selected_epistle | Chosen Epistle/Rev reference | Selection logic |
| selection_priority | Ordered rules: direct > strong TSK > fallback | Spec / selection code |
| used_refs | Set of previously used cross-refs (to prefer novelty) | Persistent state |
| topic_query | Free-text topic in topic mode | User input |

## Constraints

- KJV text is public domain; use verified source.
- Cross-reference data: open TSK-derived set from CrossReferences-org (CC BY 4.0) or equivalent.
- Selection must be transparent and high-signal; avoid weak or forced links.
- Flashcard UI must stay minimal (passage + reference + short note + Next/Menu).
- Progress persistence required so “next day” is deterministic.
- Long OT chapters: allow key-verse summary option or multi-card split if needed, but prefer full chapter when feasible.
- Topic search: start with keyword + TSK anchors; later semantic if needed.
- No copyrighted modern translations by default (optional pairing on demand only if licensed or public domain).

## Commit history (key milestones)

| Commit | What |
|---|---|
| 0a07368421bdc9571b35af7fa2b6e51f5836649d | Initial RMAD (AA/DA/SSA) |
| (this commit) | Initial SPEC.md created from SSA decisions |

---

_Update this spec in the same commit as any architectural change._
