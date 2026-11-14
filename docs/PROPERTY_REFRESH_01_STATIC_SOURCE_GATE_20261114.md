# PROPERTY REFRESH TEST 01 — Static source gate, 2026-11-14

**Scope:** Read-only source assertions on GitHub feature branch `feature/sweeper-v2.2.34-existing-target-repair`. No Inventor compilation, execution, Vault access, file mutation or Python unittest run. **NOT QUALIFIED.**

## Inputs
- `scripts/ilogic/experiments/BEEXCITED_PROPERTY_REFRESH_TEST_01_v0_1_0.iLogicVb` blob `aaf031f578fba133d81feab6884ff35c85632b6d`
- `scripts/ilogic/experiments/BEEXCITED_PropertyRefreshPure.iLogicVb` blob `064b719a12b1e6ff5f34fefb0a39075b4bc9008d`

## Executed source assertions
JavaScript string/regular-expression assertions against complete file contents fetched through the GitHub connector (not an iLogic compiler). Results:

| Assertion | Observed |
|---|---|
| Standalone explicitly blocks APPLY | true |
| Standalone references `BEEXCITED_PropertyRefreshPure.` | false |
| Pure library declares `ReplaceLeadingProjectPrefix` | true |
| Pure library contains no `InputBox`, `MessageBox` or `ThisApplication` | true |
| Standalone references `AllReferencedDocuments` | true |
| Standalone references `TopDirectoryOnly` | true |
| Standalone calls canonical `ExecutePropertyRefresh(` | false |
| Standalone declares local `Sub Main()` | true |
| Pure library contains `Inventor.`, `Documents.Open` or `Save2(` | false |

**Interpretation:** The standalone entry has not been connected to the proposed canonical shared engine. The pure module is an independent planning component, not evidence of integrated reuse. Text assertions do not establish control-flow safety, API correctness or actual test coverage. A missing literal reference could also reflect a different calling convention; inspect complete source before refactoring.

## Next bounded change
Implement a single versioned **read-only preview** core called by two thin entry wrappers, with adapters and structured per-file outcomes. Preserve existing standalone candidate as reference and keep APPLY blocked. Execute offline regression tests and record exact commands/results; require Inventor/Vault qualification before enabling any mutation. Keep Existing Target Repair separate; do not change main/production.
