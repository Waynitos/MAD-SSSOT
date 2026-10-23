# Topic Type: Script Audit

**Use for:** Reviewing Python, iLogic, LISP, PowerShell, AutoIt, or other scripts for correctness, robustness, and completeness.

## AA Framing
Analyse the script and build the strongest case for what it does well. Cover: does it achieve its stated goal, is the logic sound, is it readable and maintainable, does it handle the expected inputs correctly? Note any particularly clean or efficient patterns.

## DA Pressure Angles
- Edge cases: what inputs or states were NOT tested?
- Error handling: what happens on failure — silent fail, crash, corrupt output?
- Boundary conditions: empty input, null values, max/min values, unexpected types
- Logic errors: off-by-one, wrong operator, incorrect condition
- Hardcoded values that should be parameters
- File/path assumptions that break on different machines or environments
- Performance: does it scale? Any O(n²) traps or unnecessary loops?
- Security: does it expose credentials, write to unsafe paths, or accept unsanitised input?
- For iLogic/LISP specifically: CAD object assumptions, document state dependencies, undo/transaction handling
- Does it leave the system in a clean state on exit or error?
- Is there a test or validation step, or does it run blind?

## SSA Requirements
- List confirmed bugs or logic errors (high confidence)
- List suspected issues that need testing to confirm (lower confidence)
- Provide corrected code or specific fix recommendations for each issue
- Rate overall robustness: Production-ready / Needs hardening / Prototype only
- Suggest the 1–2 highest-priority fixes if the user can only do a few

## Checklist
→ checklists/script-audit.md (to be created)

## Note
This topic type requires the actual script to be provided. The DA cannot pressure-test what it cannot read. Always paste the full script before running this topic type.
