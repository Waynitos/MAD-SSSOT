# v2.2.34 Frame Generator GUID / XML identity investigation

User asks whether SUPER CLEAN SWEEPER already uses GUIDs and whether Frame Generator XML can be investigated. **Existing implementation use of GUIDs has not been confirmed by source inspection in this note.** Search actual branch code before asserting coverage.

## Read-only research track
1. Audit current Indexer, Copy Planner, Executor and diagnostic manifests for use of GUIDs, Inventor Document.InternalName, DocumentDescriptor/FileDescriptor, ReferenceKeyManager, occurrence identity, and any existing metadata/attribute inspection.
2. On a disposable minimal frame, inventory documented API identities and parent-child references for source and copied frame, skeleton, generated members and master sketch. Differentiate document lineage identity from occurrence/entity reference keys and any Frame Generator-specific identity.
3. Inventory **documented** AttributeSets, custom iProperties, supported metadata and any actual sidecar XML or manifest files. Inventor IAM/IPT files are not assumed to be XML. Record provenance, paths, schema evidence and before/after differences. No undocumented binary editing or XML mutation.
4. Compare source vs target after supported Copy Design baseline and after controlled experimental copy; flag retained old-project paths, unresolved edges, unexpected identity changes and lost editability.
5. Correlate metadata differences with skeleton dirty-state and save-context prompts after lower-level subassembly replacement.
6. Capture API version, exceptions, read-only/Vault state, timings, and a manual field for native dialog wording.

## Guardrails
- No assertion that a Frame Generator-specific member GUID or hidden XML manifest exists until observed/documented.
- Do not assume Document.InternalName must change on copy; validate actual Autodesk semantics.
- Do not treat reference keys as portable file identifiers without context.
- No writes to original source, undocumented metadata, or production/main.
- Gate any repair on proven supported Inventor 2025 APIs and disposable-copy tests.

## Success
Produce a source-to-target identity/reference graph diff that explains whether the frame retains stale skeleton/member relationships, with a precise diagnosis of which identity or reference layer is implicated.
