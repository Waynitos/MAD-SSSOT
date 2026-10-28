# PLU Pre-Code Search Protocol v1.0
## Research-First Before Writing Non-Trivial Code

---

## PURPOSE
Before writing code for a non-trivial function, always search for real working examples first. The cost of a 2-minute search that finds nothing is zero. The cost of skipping a search that had the answer is hours of failed test cycles.

**Origin:** Inventor drawing model-reference replacement — multiple approaches failed over a long session; a single Autodesk forum post solved it immediately. The lesson: search first.

---

## TRIGGER: PRESEARCH

When a session involves writing code, a script, iLogic, LISP, Python, PowerShell, AutoIt, or any automation — Claude evaluates the task before writing a single line:

### Is it trivial?
A task is **trivial** if ALL of the following are true:
- It uses only standard language syntax (loops, conditionals, string ops)
- It requires no application API, COM object, or proprietary SDK
- It has no silent/background execution requirement
- Claude is confident in the exact method from prior known examples in this session

If trivial → write the code directly.

### Is it non-trivial?
A task is **non-trivial** if ANY of the following are true:
- It invokes an application API (Autodesk Inventor API, AutoCAD COM, Vault API, Windows API, etc.)
- It requires silent/background execution (no UI, no dialogs, headless mode)
- It manipulates file internals (DWG, IPT, IDW, PDF generation, etc.)
- It involves interop between applications
- It requires specific method names Claude is not certain of
- A previous attempt in this session already failed

If non-trivial → **PRESEARCH FIRST**.

---

## PRESEARCH PROCEDURE

### Step 1 — Formulate search queries
Claude generates 2–3 targeted search queries covering:
- The specific function/outcome (e.g. "replace model reference inventor drawing silently")
- The specific API or tool (e.g. "Inventor API DrawingDocument ReferencedDocumentDescriptor")
- Forum/community angle (e.g. "Autodesk forum inventor ilogic update model reference vba")

### Step 2 — Search
Claude runs WebSearch (extended mode) on all queries simultaneously.

Priority sources (in order):
1. Autodesk Forums (forums.autodesk.com)
2. Autodesk Developer Network / API docs
3. GitHub repositories with working examples
4. Stack Overflow
5. CAD/engineering community blogs and tutorials

### Step 3 — Report findings BEFORE writing code
Claude outputs a **PRESEARCH REPORT**:

```
## PRESEARCH REPORT — [Function]

### Query used
[search terms]

### Best example found
Source: [URL]
Method: [specific API call / approach identified]
Confidence: HIGH / MEDIUM / LOW
Notes: [anything relevant — version-specific, caveats, etc.]

### Alternative approaches found
- [Alt 1 + source]
- [Alt 2 + source]

### Recommendation
[Which approach to try first and why]
```

### Step 4 — User confirms, then Claude writes
User reviews the PRESEARCH REPORT and confirms approach. Claude then writes code **based on the confirmed real example**, adapting it to the project's specific requirements.

---

## RULES

1. **No code before search on non-trivial tasks.** This is the protocol, not a suggestion.
2. **Extended search mode** for domain-specific API queries — standard mode misses forum posts.
3. **Cite the source in the code comment.** Every code block that implements a searched solution includes a `# Source:` or `' Source:` comment with the URL.
4. **If search returns nothing useful** — Claude states this clearly, proposes a logical approach, and flags it as unverified. The attempt is logged so if it fails, a deeper search is the next step (not another guess).
5. **Failed approaches get logged in session context.** If a searched approach is tried and fails, that approach + reason is added to working notes so it is not retried.
6. **Agent option:** For complex multi-API tasks, spawn a `general-purpose` research agent with the PRESEARCH queries to run in parallel while Claude prepares the code scaffold. This is optional — default is Claude runs the search inline.

---

## DOMAIN-SPECIFIC SEARCH TIPS

| Domain | Best starting source |
|---|---|
| Autodesk Inventor API | forums.autodesk.com + Autodesk Developer Network |
| AutoCAD / LISP | Autodesk forums + theswamp.org + cadtutor.net |
| Autodesk Vault API | Autodesk Developer Network |
| Python file/PDF | PyPI docs + Stack Overflow |
| PowerShell | Microsoft Learn + Stack Overflow |
| AutoIt | autoitscript.com/forum |
| Windows COM/API | Microsoft Learn + pinvoke.net |

---

*Part of PROJECT-LAUNCH-Plus. Fetched via PLU sub-file index.*
*Version: 1.0 | 2026-10-28*
