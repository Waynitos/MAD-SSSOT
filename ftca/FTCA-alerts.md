# FTCA-alerts.md — FTCAgent Alert Definitions & Thresholds
# Fine Tooth Comb Agent | Waynito AI Usage Monitor
# Version: 1.0 | Created: 2026-10-24

---

## ALERT FORMAT (in-session)

```
🔍 FTCAgent ALERT [TYPE]
Observation: [what was detected]
→ Suggestion: [specific actionable redirect]
→ Effort: [Low / Medium / High to implement]
Action: [ Log to FTCA | Run MAD on this | Dismiss ]
```

---

## ALERT TYPES & TRIGGERS

### REPETITION
**Trigger:** Same data/content pasted or typed manually across 2+ sessions or 3+ times in one session
**Examples:**
- Same GitHub repo URL typed repeatedly → "Store in PROJECT-CONFIG.md, PLU fetches it automatically"
- Same code block pasted multiple times → "Save as a Project Doc or a reusable snippet in a skill"
- Same project details re-entered → "Add to memory or Project Instructions once"

**Threshold:** 2 occurrences across sessions, 3 in single session

---

### TOOLING
**Trigger:** User performing a task manually that a Claude feature or better tool handles natively
**Examples:**
- Building colour palettes in chat → "Use Claude Design artifact for live preview and iteration"
- Formatting tables manually → "Use Claude Sheets artifact or ask for CSV output"
- Writing repetitive boilerplate → "Create a skill for this workflow"
- Describing a UI layout in prose → "Use Claude Design or Whiteboard artifact"
- Manually tracking decisions → "Project Doc with a decisions table auto-updates each session"

**Threshold:** Immediate — fire on first observation if the better tool clearly applies

---

### ADVANCEMENT
**Trigger:** New Claude/AI capability released that matches a recurring workflow Waynito does manually or in another tool
**Sources checked:** Claude release notes, Anthropic blog (fetched weekly via digest)
**Profile match areas:**
- Engineering/CAD automation (Inventor, AutoCAD, Vault)
- LISP, Python, PowerShell, AutoIt, JavaScript scripting
- File/PDM management workflows
- Spanish learning tooling
- MAD framework and knowledge base management

**Threshold:** Fire when a new feature maps clearly to a known workflow pattern from FTCA-behaviour.md

---

### GAP
**Trigger:** Claude feature exists, is clearly relevant to Waynito's profile, and has NEVER appeared in FTCA-behaviour.md features-used log
**Watch list (seeded from profile):**
- [ ] Scheduled Tasks (weekly digests, morning brief)
- [ ] Claude Design artifact (branding, UI mockups)
- [ ] Artifact database capability (persistent shared state)
- [ ] Claude in Chrome (web scraping, form automation)
- [ ] Artifact sharing/publish (shareables for team)
- [ ] Morning brief skill
- [ ] Skills (custom reusable instruction sets)
- [ ] MAD runs (structured debates on decisions)
- [ ] Voice input (if available)

**Threshold:** Fire in weekly digest if feature unused for 4+ weeks and relevance score is HIGH

---

### MAD-TRIGGER
**Trigger:** A decision or behaviour pattern is complex, contested, or has been revisited 3+ times
**Examples:**
- 4+ sessions discussing the same tool choice
- Conflicting approaches to a recurring workflow
- A "should I use X or Y" that keeps coming back

**Threshold:** 3 revisits → suggest MAD run; 5 revisits → strongly recommend MAD run

---

## WEEKLY DIGEST FORMAT

Fired every Saturday (Brisbane time) via Scheduled Task.

```
# 🔍 FTCAgent Weekly Brief — [Date]

## 🏆 Champion Calls
[2-3 things Waynito did well this week — good AI usage patterns worth reinforcing]

## 📈 Enhancements to Consider
[2-3 specific suggestions keyed to this week's behaviour log]

## 🆕 AI Advancements This Week
[New Claude/AI features or releases relevant to Waynito's profile]

## ⚠️ Open Alerts
[Any unresolved alerts from the week]

## 📊 Feature Usage This Week
Used: [list]
Still unused (high relevance): [list from GAP watch list]
```

---

## FTCA OBSERVATION PROTOCOL (for Claude to follow each session)

1. **Session start:** Fetch FTCA-behaviour.md from GitHub. Scan last 3 entries for REPETITION patterns before session begins.
2. **During session:** Monitor for TOOLING and REPETITION alerts. Fire inline if threshold met.
3. **Session end:** Append new OBSERVATION block to FTCA-behaviour.md and push to GitHub.
4. **Weekly (Saturday):** Run digest — fetch FTCA-behaviour.md, scan all entries from past 7 days, check AI advancement sources, produce digest artifact or doc.
