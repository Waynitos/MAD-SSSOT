# SSA-output.md — Synthesiser Verdict

## Topic: Daily Bible Cross-Reference Reading Project (KJV)

### Synthesis

The Advocate correctly identifies the unique value: making the Bible's dense internal cross-referencing (especially OT ↔ Psalms/Proverbs ↔ Gospels ↔ Epistles) experientially visible in a daily rhythm, while advancing through the OT. The Devil's Advocate correctly identifies the central risk: poorly defined or weak cross-reference selection will produce low-value output and high implementation cost.

### Verdict

**Proceed, but with constrained, transparent selection rules and a phased approach.**

### Locked Architectural Decisions

1. **Daily Mode (Primary)**  
   - Advance one OT chapter per day (start: Genesis 1).  
   - For that chapter, select **one** reference each from:  
     - Psalms or Proverbs  
     - Gospels  
     - Letters to churches or Revelation  
   - Selection priority: (a) direct quotation / clear allusion, (b) strong thematic match documented in TSK or equivalent, (c) fallback to a well-known related passage with a note that it is thematic rather than direct.  
   - Prefer non-repeated references where possible; allow repeats only when no stronger unused option exists.  
   - Present as four sequential flashcards (OT → Ps/Prov → Gospel → Epistle/Rev) with clear "Next" and a persistent "Menu" button.

2. **Topic Mode (Secondary)**  
   - Free-text topic entry.  
   - Return first (or strongest) mention in OT, then Psalms/Proverbs, then Gospels, then Epistles/Revelation.  
   - Show a short note on why each was selected.

3. **Presentation**  
   - Flashcard-style popup / modal.  
   - Minimal UI: passage text (KJV), reference, optional one-line connection note, Next / Menu.  
   - Menu options: Continue next day | Custom topic | (later) View progress.

4. **Data**  
   - KJV (public domain).  
   - Open TSK-derived cross-reference data (e.g., CrossReferences-org JSON).  
   - Precompute the first year of daily sets for quality control before full automation.

5. **Delivery Options (phased)**  
   - Phase 1: Claude Project with custom instructions + memory for progress + on-demand generation.  
   - Phase 2: Simple web flashcard interface or scheduled Automation that delivers the day's set.  
   - Phase 3: Full offline-capable app if usage justifies it.

### Residual Uncertainty / Next Best Alternative

- If selection quality cannot be made consistently high, fall back to a simpler parallel reading plan (OT chapter + fixed Ps + Gospel + Epistle rotation) without dynamic cross-ref matching.  
- Optional: pair each KJV passage with a modern translation on demand for readability.

### Next Actions

- Create project spec doc (per SESSION_STARTUP_PROTOCOL).  
- Prototype selection logic on Genesis 1–5 using open TSK data.  
- Define exact flashcard UI tokens (consider PHONICSPlus if branded).  
- Commit this MAD run (done).

**SSA Decision: Build the constrained version. The interconnection insight is worth the effort if selection is transparent and high-signal.**
