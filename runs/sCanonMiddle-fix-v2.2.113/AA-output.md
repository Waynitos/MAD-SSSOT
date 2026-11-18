# AA-output.md — Advocate Position
## MAD Cycle: `DetectStringAnomalies` sCanonMiddle Fix (v2.2.113-FIRST-TOK)

---

## Executive Summary

The fix is mechanically correct, narrowly scoped, and directly addresses a confirmed real-world defect observed in the 18/11/2026 run. Without it, the STRING-SUGGEST mechanism would have proposed re-inserting a stale project code into 43 already-correct filenames — a silent, user-approved corruption. The fix correctly strips the embedded PJ token from `sCanonMiddle` using a targeted regex and falls back safely to `""` when no clean 4-digit token can be recovered.

---

## Mechanical Correctness Analysis

Given GA filename: `PJ00204-PJ00190-3430-V0.iam`

The original extraction logic found the span from the first `-` to the first `V`, yielding:

```
sCanonMiddle = "-PJ00190-3430-"
```

This is factually wrong as a "middle token" reference. The GA's true discriminating middle token is `-3430-` — the numeric job sub-code. The embedded `PJ00190-` is a legacy double-prefix artefact from an earlier project code, not part of the canonical middle.

The fix applies the guard:

```vb
If sCanonMiddle.ToUpper().Contains("-PJ") OrElse sCanonMiddle.ToUpper().StartsWith("PJ") Then
    Dim oMidNumRe As New System.Text.RegularExpressions.Regex("-(\d{4})-")
    Dim oMidNumM As System.Text.RegularExpressions.Match = oMidNumRe.Match(sCanonMiddle)
    If oMidNumM.Success Then
        sCanonMiddle = "-" & oMidNumM.Groups(1).Value & "-"   ' → "-3430-"
    Else
        sCanonMiddle = ""
    End If
End If
```

Walking through the regex on the actual value `-PJ00190-3430-`:

- Pattern `-(\d{4})-` looks for a hyphen, exactly four digits, then another hyphen
- In `-PJ00190-3430-`, the pattern matches at position 8: `-3430-`
- `oMidNumM.Groups(1).Value` = `"3430"`
- Result: `sCanonMiddle = "-3430-"` ✓

This is precisely the correct canonical middle token. The fix recovers the right value from a contaminated extraction.

---

## Why the Trigger Condition `.Contains("-PJ")` Is Correctly Scoped

The guard fires *only* when the extracted `sCanonMiddle` itself contains a PJ-style project code embedded within it. Normal GAs — `PJ00204-3430-V01.iam` — produce a clean `sCanonMiddle = "-3430-"` that contains no `-PJ` substring, so the guard is never entered. The condition is a targeted surgical instrument, not a broad sweep that could interfere with standard assemblies. It is impossible for this guard to misfire on a legitimately clean middle token.

---

## Why Safe-Fallback to `sCanonMiddle = ""` Is the Right Failure Mode

If the regex finds no 4-digit hyphenated token inside the contaminated `sCanonMiddle`, the code sets `sCanonMiddle = ""`. This means no STRING-SUGGEST is generated for the middle token. Producing zero suggestions is strictly safer than producing a wrong suggestion. The user sees nothing anomalous suggested for the middle, and no filenames are touched. The alternative — leaving `sCanonMiddle = "-PJ00190-3430-"` — produces an actively harmful suggestion. Silence is always preferable to a suggestion that corrupts already-correct data.

---

## FIRST-TOK Comparison as Defense-in-Depth

The FIRST-TOK comparison (lines 3436–3444) adds a second independent layer. When comparing each file's `sMiddle` against `sCanonEq`, only the **first hyphen-delimited token** of `sMiddle` is compared. This means that even if `sCanonMiddle` slipped through the guard with a contaminated value, the comparison logic would only match files whose first middle token matches — significantly limiting blast radius. The two layers (guard + FIRST-TOK) are complementary: the guard prevents a wrong canon from being established; FIRST-TOK limits the damage if one ever slips through.

---

## Evidence from the 18/11 Run

The 18/11/2026 run log directly confirms the pre-fix defect: the system generated the STRING-SUGGEST `-3430- -> -PJ00190-3430-` for 43 files. Those 43 files already had the correct token `-3430-`. Accepting that suggestion would have inserted the obsolete project prefix back into every one of them, requiring a manual correction pass across 43 assembly members. The fix, applied to that exact GA and that exact `sCanonMiddle` value, produces `-3430-` as the canon — generating either no suggestion (correct files match canon, no anomaly) or a suggestion pointing *toward* `-3430-`, not away from it.

---

## Why This Fix Is Preferred Over Alternatives

**Alternative A — Strip all non-numeric tokens from `sCanonMiddle`:** This would be over-broad. Some valid middle tokens contain alpha characters (e.g. revision suffixes in certain naming conventions). The PJ-specific guard targets only the known contamination pattern without disturbing other formats.

**Alternative B — Use the drawing filename as canon source instead of GA:** The GA is the structural root of the assembly tree and is the correct authority for naming conventions. Switching to the drawing would add a dependency on a file that may not always be present, and would not address the root cause — the double-prefix GA pattern exists and must be handled wherever GAs are used as canon.

**Alternative C — Warn and skip rather than auto-correct:** Appropriate for edge cases, but `""` fallback already achieves this by suppressing the suggestion entirely. No additional warning UI is needed for a silent non-suggestion.

---

**Verdict (AA position):** The fix is correct, safe, minimal in scope, confirmed by real run evidence, and superior to all identified alternatives. It should be retained in v2.2.113 without modification.
