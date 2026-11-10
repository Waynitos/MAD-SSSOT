# Inventor 2025 iLogic — WinForms DefaultFont compile failure

**Recorded:** 2026-11-11
**Project:** iLogic ASSASSIN / Drawing View Dimension Investigator
**Status:** INVESTIGATING — fix proposed, Inventor recompilation not yet confirmed
**Source:** User-provided Inventor iLogic compiler output for rule `Test2` in `PJ00143-GTA-3431-6-00401.dwg`

## Observed failure
At line 109 (reported twice):
```
Reference required to assembly 'System.Drawing.Common, Version=8.0.0.0, Culture=neutral, PublicKeyToken=cc7b13ffcd2ddd51' containing the type 'Font'. Add one to your project.
```

## Root cause (high confidence)
The generated rule assigned `txt.Font = System.Windows.Forms.Control.DefaultFont` to a Windows Forms TextBox. The Font property introduces a System.Drawing.Common assembly dependency not resolved by the user's Inventor 2025 iLogic compiler environment. The existing `scripts/ilogic/ILOGIC_EDIT_PROTOCOL.md` already identifies System.Drawing Font-related APIs as blocked. This was a preventable protocol regression.

## Minimal corrective action (PROPOSED)
Remove the entire `txt.Font = System.Windows.Forms.Control.DefaultFont` assignment. Leave the TextBox default font in place. Do **not** add assembly references merely to support cosmetic formatting.

## Validation
- **VERIFIED:** Compiler error text supplied by user; offending statement identified in delivered source.
- **NOT TESTED:** Recompilation in Inventor 2025 after removal.
- **NOT TESTED:** Full Drawing View Dimension Investigator runtime and API compatibility.
- **No production files changed** by this knowledge entry.

## Regression guard
For future iLogic deliveries, scan the **entire** rule for `.Font`, `System.Drawing`, `Control.DefaultFont`, `ForeColor`, `BackColor` and other blocked APIs; cross-check `scripts/ilogic/ILOGIC_EDIT_PROTOCOL.md`. Confirm complete `Sub Main`/helper blocks and distinguish static review from actual Inventor compilation. Retain read-only inspection behavior.

## Next action
Recompile `Test2` after deleting the Font assignment. Capture result; only mark TESTED or VERIFIED on real evidence. If new errors appear, append distinct failure evidence rather than assuming this fix resolves all issues.
