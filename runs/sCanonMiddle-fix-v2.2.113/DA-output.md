# DA-output.md — Devil's Advocate: `sCanonMiddle` Fix in `DetectStringAnomalies` (v2.2.113-FIRST-TOK)

## Executive Summary

The proposed fix patches a narrow symptom — a double-prefix GA filename — using a regex that embeds brittle assumptions about digit count and naming conventions that are nowhere enforced. When those assumptions break, the failure mode is *worse* than the original bug: silent suppression of all suggestions, causing the entire sweep to miss its rename targets with no warning to the user. A more robust fix already exists in the function's own parameter list and is not used.

---

## Failure Mode 1: The 4-Digit Assumption Is Undocumented and Fragile

The regex `-(\d{4})-` requires the equipment number to be exactly 4 digits, bounded by dashes. This is described as a "convention, not enforced." In practice:

- A GA named `PJ00204-PJ00190-343-V0.iam` (3-digit equipment number, perfectly valid under the convention) produces `sCanonMiddle = "-PJ00190-343-"`. The regex finds no `-\d{4}-` match. `sCanonMiddle = ""`. The suggestion engine emits nothing. The user sees a blank form, clicks OK, and every file containing `-343-` is left unrenamed. The sweep completes successfully — and silently fails its entire purpose.
- A 5-digit equipment number (`-34300-`) suffers identically.
- There is no log message, no MsgBox, no indicator that the canon extraction failed. The user has no path to diagnosis.

This is not an edge case in the abstract. The same run environment that generated `PJ00204-PJ00190-3430-V0.iam` (a double-prefix corruption) is exactly the environment likely to produce other non-standard filenames.

---

## Failure Mode 2: Left-to-Right Regex Scanning Can Match the Wrong Token

For `"-PJ01234-5678-"`, the regex engine scans left-to-right and finds `-1234-` (a 4-digit substring bounded by dashes at positions within `PJ01234`). It would return `sCanonMiddle = "-1234-"` — a fragment of the PJ code, not the equipment number. This yields incorrect `STRING-SUGGEST` entries that propose replacing a PJ-code fragment with nothing, potentially corrupting file names across the entire assembly tree.

The fix's author traced one specific GA format (`PJ00204-PJ00190-3430-`) and confirmed it safe. That is not a proof of correctness; it is a test of one case.

---

## Failure Mode 3: Non-PJ Embedded Tokens Bypass the Guard Entirely

The `.Contains("-PJ")` condition gates the entire correction block. Any GA with a non-PJ embedded token — `-OLD-`, `-BACKUP-`, `-REF-`, `-COPY-`, `-OBSOLETE-`, or a previous project's custom token — will not trigger the fix. `sCanonMiddle` will be left as the full corrupted string (e.g., `"-OLD-3430-"`), and the suggestion engine will produce wrong `STRING-SUGGEST` entries based on a canon that includes noise tokens.

The fix solves the PJ-double-prefix case. It does not solve the class of problem.

---

## Failure Mode 4: Root Cause Not Addressed — the Fix Rewards Corrupt Input

The double-prefix GA (`PJ00204-PJ00190-3430-V0.iam`) exists because an earlier rule run failed to rename it correctly. The fix teaches the suggestion engine to tolerate and work around this corruption. The correct architectural response is to detect the malformed GA, alert the user, and refuse to derive canon from it. Instead, the fix silently normalises corrupted input and proceeds — increasing the risk that downstream logic operates on a filename that is already wrong.

---

## Failure Mode 5: Silent Suppression Is Categorically Worse Than a Wrong Suggestion

The original bug produced an incorrect `sCanonMiddle = "-PJ00190-3430-"`. That wrong value would appear in the STRING-SUGGEST form, the user would see it, recognise it as wrong, and correct or skip it. User in the loop; recoverable.

The fix's failure mode — `sCanonMiddle = ""` — produces no suggestion at all. The user sees a clean form, assumes the tool found nothing to fix, and approves. Files go unrenamed. The error is invisible at the point of failure and only discovered later (if at all) when renamed assemblies still reference stale sub-part numbers.

Visible wrong output is safer than invisible no output in a tool whose primary UX contract is "suggest what needs fixing."

---

## Failure Mode 6: The Better Fix Is Already in the Function Signature

`DetectStringAnomalies` already accepts `sDwgEntryPath` as a parameter and uses it for equipment-number extraction (lines 3499–3505). The drawing filename is user-entered and guaranteed correct — it is the input that initiated the sweep. Deriving `sCanonMiddle` from the drawing filename rather than the GA filename eliminates the double-prefix problem entirely, requires no PJ-stripping regex, and is robust to all equipment number lengths and all GA naming corruptions.

The proposed fix is a workaround. The drawing-file derivation is the correct fix. Implementing the workaround now creates a false sense of resolution and reduces the pressure to implement the robust solution.

---

## Risk Assessment

| Scenario | Outcome under proposed fix |
|---|---|
| 3- or 5-digit equipment number | Silent suppression; sweep renames nothing; no error |
| PJ code where last 4 digits match `-\d{4}-` pattern | Wrong canon fragment used; files misrenamed |
| Non-PJ embedded token in GA name | Corrupted canon used; wrong suggestions emitted |
| Correctly named GA | Fix works as intended |

The fix is correct for exactly the case that was tested. It is wrong or silent for the broader class.

---

## Recommendation: Revise — Do Not Merge As-Is

Reject the fix in its current form. The minimum acceptable revision is:

1. Add an explicit warning/log when the regex fails to match, so silent suppression is detectable.
2. Document the 4-digit assumption as a known limitation with a TODO.
3. Open a tracked issue to migrate `sCanonMiddle` derivation to `sDwgEntryPath` as the authoritative canon source.

The clean solution — deriving canon from the drawing filename — should be scheduled as the follow-on task. The current fix may ship as a temporary patch only if the warning (point 1) is added, so users are never silently left without suggestions.
