# Frame Generator save-in-context prompt — diagnostic hypothesis

User observation (Inventor 2025): a Frame Generator skeleton part repeatedly appears in save prompts or Inventor reports that it must be saved in the context of its frame assembly (exact wording not yet captured).

**Do not assume root cause.** This may involve assembly-context associations, adaptivity, dirty-document propagation, skeleton/member references, Frame Generator metadata, or Vault/write permissions. A prompt alone does not prove broken links.

## Add to v2.2.34 sprint
- Capture exact prompt wording, document name/path, active assembly, Inventor version, project (.ipj), Vault state, and whether this occurs before or after Copy Design.
- Compare dirty flags and save order for master sketch, generated reference skeleton, frame subassembly, generated members, and top-level GA. Note which document Inventor marks modified after opening, updating, refreshing, and saving.
- Record actual file reference descriptors and ownership before/after copy; detect references back to old project and changes to assembly-context metadata where exposed by supported APIs.
- Reproduce on disposable copies: ordinary frame, nested frame, copied frame with original skeleton reference, read-only skeleton, checked-out skeleton, missing reference, and mismatched project file.
- Determine whether saving the parent assembly first, the skeleton first, or a controlled update changes the prompt, without imposing an unverified global save order.
- Treat repeated skeleton save/context prompts as a **blocking integrity diagnostic** during repair preflight until understood; do not silently suppress, automatically save, or force refresh.
- Log save prompts/dirty-state transitions and frame context in the existing v2.2.33 profiling and diagnostic output.
- Inventor 2025 validation required; this document is an observation and test plan only.
