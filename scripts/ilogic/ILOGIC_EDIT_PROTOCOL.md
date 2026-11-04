# iLogic Edit Protocol

Standing rules for any person or AI tool (Grok, Claude, Cursor) editing iLogic
rules in `scripts/ilogic/`. Repo-wide workflow rules (whole files, one file per
script, no dated copies, LF only, never force-push) live in `AGENTS.md` and
`CLAUDE.md`.

## 1. Structure

- Only `Imports` or `AddReference` lines may sit above `Sub Main`.
- `Sub Main()` is mandatory and must be the first executable.
- Helper Subs, Functions and Consts come AFTER `Sub Main` and before the first `Class`.
- Nesting a Sub or Function inside another Sub is not valid VB. Never do it.
- No module-level `Dim` declarations (outside a Sub or Function).
- Do not add `Imports System.IO` or `Imports System.Windows.Forms` (pre-imported).

## 2. Scope

- Variables declared inside an `If` block are not visible outside it. If a value is
  used after the block, declare it just before the `If`.
- Never declare the same variable name in both branches of an `If`/`Else`, or in an
  inner block when an enclosing block already has it ("Variable hides a variable in
  an enclosing block"). Declare once in the outer scope.
- Declare loop counters and loop control variables once, outside the loop. No `Dim`
  inside `For` loops, and never re-declare a loop variable from an enclosing scope.
- One statement per line in new code. No colon chaining.
- Never name a variable after a VB keyword, case-insensitively (`oR`, `oN`, `oMod`
  match `Or`, `On`, `Mod`).
- Avoid `ByRef` parameters captured in lambdas.

## 3. Blocked APIs

- `System.Drawing.Primitives` is blocked: no `Color`, no `SystemColors`.
- Never use `ForeColor` or `BackColor` on any control. Use text for visual cues.
- The `System.Drawing.Font` constructor is blocked.
- `Button.ToolTipText` is not a member in this sandbox.

## 4. Content Centre check

- Do not use `DocumentSubType = kCCPartDocumentSubType`. The constant is not in scope,
  and `DocumentSubType` is an object, so `=` against it does not compile.
- Do not use `DocumentSubType.ToString().Contains(...)`. It returns a COM type name
  and never matches.
- Use `oDoc.DocumentType = DocumentTypeEnum.kPartDocumentObject AndAlso
  oDoc.ComponentDefinition.IsContentMember`, or a path heuristic (Content Center
  library folder in the full path).

## 5. Other recurring fixes

- Use `For Each ... As Object` for non-primitive loop variables (late binding,
  Option Strict Off).
- Use `ReferencedDocumentDescriptors` / `ReferencedFileDescriptors`, not
  `ReferencedDocuments`, when walking references.
- Strip the `<` state tag from descriptor paths before comparing or opening them.
- Fully qualify `System.Environment.GetFolderPath` and
  `System.Environment.SpecialFolder` (iLogic host ambiguity).
