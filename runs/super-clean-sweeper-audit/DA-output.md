## DA: Case AGAINST Super Clean Sweeper Architecture

### 1. The GUID Capture Is Probably Wrong

The architecture assumes `SaveAs(newPath, True)` generates a fresh GUID in the copy, so `CS_SourceGUID` must be read from `oDoc.InternalName` *before* the call. This assumption is unverified. Autodesk's documentation on `SaveCopyAs` behaviour is inconsistent across versions. If the copy in fact *preserves* the original GUID (which some Inventor versions do for SaveCopyAs=True), then `CS_SourceGUID` correctly records the source — but the new file also carries that same GUID, creating a duplicate-GUID collision in Vault. Two distinct physical files sharing one internal GUID will cause Vault to treat them as the same document, breaking check-in, version history, and where-used queries silently and permanently. This is not a recoverable error; it corrupts the Vault database for both files.

### 2. Silent Provenance Loss on Open Failure

After `SaveAs(newPath, True)`, the architecture opens the new file separately to write provenance properties. If that open fails — file lock, Inventor memory pressure, anti-virus scan holding the file — the exception must be caught and the file skipped, or the whole rule aborts. Either way, the destination file exists on disk with no CS_ properties. The skip guard on re-run reads `CS_CopyProject`; it will be blank, so the file gets re-processed, overwriting whatever the user has already edited in that copy. Silent partial failure leaves the file set in an indeterminate provenance state with no log entry pointing to which files were missed.

### 3. WalkTree Memory Accumulation Is a Real Crash Risk

WalkTree opens documents recursively and does not explicitly close them between visits. On a 200-file assembly, Inventor will accumulate open documents in memory throughout the walk. At typical `.iam` sizes this reaches 2–4 GB of working set before Phase 3 begins. Inventor's COM layer is single-threaded; there is no yield point. The rule will either exhaust memory and crash mid-run — leaving a partially-copied file set with no rollback — or trigger Inventor's internal document cache eviction, which can silently change the state of `ReferencedDocumentDescriptors` mid-iteration, causing WalkTree to miss branches or visit nodes twice.

### 4. Phase 3 ReferencedFileDescriptors Does Not Handle DART SHUT

The deliberate switch from `ReferencedDocumentDescriptors` (used in WalkTree to handle `<` state tags) to `File.ReferencedFileDescriptors` in Phase 3 is a correctness gap. DART SHUT files appear in `ReferencedDocumentDescriptors` with their path stripped of the `<` prefix, but `ReferencedFileDescriptors` reflects the raw on-disk reference, which may still carry the state tag or simply be absent from the collection. Any sub that was DART SHUT during the walk will not have its internal FileDescriptor rewritten in Phase 3, leaving it pointing at the old-prefix path. The file appears valid until someone opens the new assembly, at which point Inventor reports missing references for exactly the components that were substituted — the ones most likely to be bespoke, non-library parts.

### 5. Non-Prefix Files Leave Broken Refs With No Warning

Library parts and non-standard components that do not match the old prefix are skipped during copy. Their new-path counterparts will have FileDescriptors pointing back to the original locations. The rule emits no warning, no list, no summary of skipped files. The first indication of the problem is Inventor's missing-reference dialog on the next open, with no connection back to the copy operation. In a 200-file tree, tracking down which references broke and why is hours of manual work.

### 6. No Rollback, No Atomicity

If the rule fails at file 150 of 200 — mid-Phase-3, mid-provenance-write, or mid-WalkTree — the destination folder contains a mix of correctly processed, partially processed, and unprocessed files. There is no transaction, no manifest of completed operations, and no cleanup path. The only safe recovery is to delete the entire destination folder and start again, discarding any manual work done on already-copied files. The architecture has no mechanism to prevent or detect this partial-completion state.
