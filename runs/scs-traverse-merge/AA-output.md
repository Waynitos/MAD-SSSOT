# AA — Merging old Traverse functions into Super Clean Sweeper

**Position:** The Super Clean Sweeper needs the old Traverse rule's occurrence-level Replace and unsuppress/re-suppress to produce the full resweep results the old rule gave.

The 11:06 run proves the SaveAs architecture works: 257 files saved, 308 refs fixed. The gap is that Phase 3 rewrites FileDescriptors in isolation, then fails to save some parent assemblies with E_FAIL. Those assemblies (E3432-8-32, -33, JC002702, JC004076, JC003438) are the ones whose children still point at the old PJ00161 paths in the post-rule tree. The old Traverse rule's ConsolidateLevel walks ComponentOccurrences on the live assembly, unsuppresses them, and does ComponentOccurrence.Replace in place. That is why it produced a fully updated GA tree. Adding a post-Phase 3 occurrence walk on the active GA that does ComponentOccurrence.Replace for any remaining old-path refs will close the gap without abandoning the SaveAs + provenance architecture.

**Recommended fix:** After Phase 3, walk the active GA's ComponentOccurrences. For any occurrence whose current path is in oActualMap and whose target exists, call ComponentOccurrence.Replace(newPath, False). Unsuppress first if needed, re-suppress after. Log each replace. Browser rename is a low-priority follow-on.
