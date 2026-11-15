# PROPERTY REFRESH TEST 01 — iLogic Assassin source comparison (2026-11-15)

**Status:** Source investigation only; NOT a qualified Inventor rule. Branch: `feature/sweeper-v2.2.34-existing-target-repair`. No main or production changes.

## Recovered original rule
`scripts/ilogic/experiments/BBn_PROPERTY_REFRESH_ONLY_PWTP_01.iLogicVb` (Friday standalone rule).

## Direct comparison
| Concern | Friday PWTP-PROP-01 | Shared-core v0.1.0 wrapper | Implication |
|---|---|---|---|
| Setter | `Inventor.PropertySet.Item(name).Value = value` in `UpdateProp` | Planned change serialized then `doc.PropertySets.Item(...).Item(...).Value = ...` | Both use the same COM property setter. No evidence the setter itself is wrong. |
| Model eligibility | Requires `CS_CopyProject = target PJ` | Requires active GA folder containment and no read-only | Friday rule may silently skip otherwise valid files due to provenance mismatch; newer wrapper may exclude nested project files outside GA folder. |
| Traversal | `Directory.GetFiles(root, pattern, TopDirectoryOnly)` | `AllReferencedDocuments` for GA | Friday rule **does not** traverse nested GA dependencies; it only scans root-level files. |
| Drawing scope | Root-level `*.idw/*.dwg` | Active drawing folder | Both limited to immediate folder, depending on selected root. |
| Drawing property | `DRAWING_NUMBER` set to filename stem, plus `REVISION`, `Revision Number`, `DRAWN`, `1st REV`, etc. forcibly reset | `DRAWING_NUMBER` only, requiring matching PJ prefix in existing value and filename | Friday rule can reset revision data; newer rule may skip if identity pattern differs. Neither proves actual title-block field mapping. |
| Model properties | `SPECIFICATION`, `Part Number`, populated `PROJECT NUMBER`, padding `DRAWING REF` and `ITEM NUMBER` | `SPECIFICATION`, `Part Number` only | Extra fields need separate approval; avoid unrelated mutations in property smoke test. |
| Save | `doc.Save2(False)` after nonzero changes | `doc.Save2(False)` in dormant APPLY | Same save call; not a demonstrated root cause. |
| Error reporting | Setter catches and logs generic `MISSING-OR-UNWRITABLE` | More detailed read failures; APPLY blocked | Friday rule suppresses actual COM exception reason, making diagnosis difficult. |
| Verification | No persisted readback | In-memory readback only | Neither proves persisted values after closing/reopening. |

## Code Reuse First directive
Use the existing `UpdateProp` and `UpdateLeadingPJ` pattern as baseline, rather than writing another independent setter. For a single backed-up checked-out file, instrument the existing setter to capture the full exception, old/new property value, `doc.Dirty` and `Save2(False)` result. Confirm actual property mapping in a known successful drawing before changing the drawing logic. After single-file verification, test GA references and drawing-folder discovery separately.

## External prior-art leads (not independently executed)
- Autodesk Community assembly properties: https://forums.autodesk.com/t5/inventor-programming-forum/updating-properties-of-all-parts-within-assembly/td-p/10873842
- Autodesk Community open drawings: https://forums.autodesk.com/t5/inventor-programming-forum/ilogic-to-update-iproperties-on-all-open-drawings/td-p/10556593
- Autodesk Community changing iProperties: https://forums.autodesk.com/t5/inventor-programming-forum/changing-iproperties-with-ilogic/td-p/12352311

## Static verification actually performed
Fetched and inspected Friday rule and existing shared-core standalone source via GitHub connector; checked concrete code for traversal, property names, setter, skip gates and save behavior. No Python tests, VB compilation or Inventor/Vault execution. Findings are hypotheses pending instrumented real-file tests.

**No APPLY enablement authorized.** Keep separate Existing Target Repair work untouched.
