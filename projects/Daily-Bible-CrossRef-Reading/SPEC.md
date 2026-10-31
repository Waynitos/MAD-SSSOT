# Daily Bible Cross-Reference Reading Project — Spec
_Last updated: 2026-10-31_

This document is the authoritative spec for the Daily Bible Cross-Reference Reading Project.
Any session working on this project must read this before making changes.

Source of architectural decisions: SSA from RMAD in runs/Daily-Bible-CrossRef-Reading-Project/ + 2026-10-31 refinement (user-selected extracts).

---

## Entry point

- Phase 1: Claude Project (custom instructions + conversation or memory for progress).
- User opens the Project and requests “today’s reading” or “next day”.
- Optional: scheduled Automation that posts the day’s set.
- Later phases: simple web flashcard UI or app.

## Step-by-step flow

1. Determine current day index (start: day 1 = Genesis 1). Persist in Project memory or user state.
2. Load the OT chapter for the day (sequential from Genesis 1 onward).
3. Rank the top 5 extracts/themes within that chapter by cross-reference density (using TSK / CrossReferences-org data). Rank highest first. An “extract” is a verse or short contiguous group of verses that share a clear theme and have concentrated references.
4. Present the top 5 ranked extracts to the user as a choice menu (with brief theme label + reference count or strength indicator). User may select 1–3 extracts to explore that day.
5. For each selected extract:
   - Select one high-signal linked passage from each category (Ps/Prov, Gospels, Epistles/Rev) using priority:
     - Direct quotation or clear allusion (highest).
     - Strong thematic match from TSK data scoped to that extract.
     - Documented fallback with note that it is thematic.
   - Prefer unused references across days where possible.
6. Present as sequential flashcards, grouped by extract:
   - For each chosen extract: OT extract card → Ps/Prov card → Gospel card → Epistle/Rev card.
   - Optional: full chapter available as a separate “Read full chapter” card or link.
7. Each card shows: KJV text, reference, optional one-line connection note.
8. Controls: “Next” advances through cards. After finishing the selected extracts, offer:
   - Choose different extracts from the same OT chapter (go back to the top-5 menu without advancing day).
   - Next day (advances day index).
   - Menu.
9. Persistent “Menu” button.
10. Menu options:
    - Continue next day (advances day index).
    - Revisit today’s OT chapter (return to top-5 extract menu).
    - Custom topic (free-text entry).
    - (Later) View progress.
11. Topic mode flow:
    - User enters topic (e.g. “God’s Joy”).
    - Return first/strongest mention in OT, then Ps/Prov, then Gospels, then Epistles/Rev, each with selection note.
    - Present as flashcards; option to return to daily mode.

## Key variable notes

| Variable | What it is | Set where |
|---|---|---|
| day_index | Integer starting at 1 (maps to OT chapter sequence) | Project memory / user state / Automation |
| ot_chapter | Current OT book + chapter (e.g. Genesis 1) | Derived from day_index |
| top_extracts | Ranked list of up to 5 extracts/themes in the current chapter by reference density | Selection logic |
| selected_extracts | 1–3 extracts chosen by the user for the current session | User choice |
| selected_ps | Chosen Ps/Prov reference(s) for the selected extract(s) | Selection logic |
| selected_gospel | Chosen Gospel reference(s) | Selection logic |
| selected_epistle | Chosen Epistle/Rev reference(s) | Selection logic |
| selection_priority | Ordered rules: direct > strong TSK (extract-scoped) > fallback | Spec / selection code |
| used_refs | Set of previously used cross-refs (to prefer novelty) | Persistent state |
| topic_query | Free-text topic in topic mode | User input |

## Constraints

- KJV text is public domain; use verified source.
- Cross-reference data: open TSK-derived set from CrossReferences-org (CC BY 4.0) or equivalent. Ranking uses reference count / density from this data.
- Selection must be transparent and high-signal; avoid weak or forced links. Extract ranking must be explainable.
- Flashcard UI must stay minimal (passage + reference + short note + Next/Menu).
- Progress persistence required so “next day” is deterministic. User can revisit the same chapter’s extract menu without advancing the day.
- Long OT chapters: top extracts are the primary path; full chapter available on demand.
- Topic search: start with keyword + TSK anchors; later semantic if needed.
- No copyrighted modern translations by default (optional pairing on demand only if licensed or public domain).
- Limit to 1–3 extracts per session to keep daily volume manageable.

## Commit history (key milestones)

| Commit | What |
|---|---|
| 0a07368421bdc9571b35af7fa2b6e51f5836649d | Initial RMAD (AA/DA/SSA) |
| ac80e743a9f4a438666aab27fc8190a16e6d07cf | Initial SPEC.md created from SSA decisions |
| (this commit) | Refinement: user chooses from top 5 extracts in OT chapter; linked refs scoped to chosen extract(s); revisit-same-chapter option |

---

_Update this spec in the same commit as any architectural change._
