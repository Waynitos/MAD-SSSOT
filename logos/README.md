# logos/ — frozen logo SPECs (single source of truth)

Owned by the LogoSpecExtractor agent. Implements the verdict in
`runs/logo-image-edit-fidelity/SSA-output.md`: the JSON spec *describes* the logo,
deterministic tooling *enforces* it. Protected elements never pass through a generative step.

Only **frozen, human-confirmed** specs are committed here. Drafts live on the bot
computer at `/workspace/logo-specs/<slug>/draft/` until confirmed.

## Layout
```
logos/
  _templates/
    extraction-prompt.md   # vision-model extraction prompt (run once per logo)
    edit-prompt.md         # general edit prompt for Grok / Claude / Imagine
  <logo-slug>/
    v1/
      SPEC.json            # frozen spec (status FROZEN, version, sha256 of sources)
      ADHERENCE.md         # protected elements, invariants, verifier thresholds
      edit-prompt.md       # general edit prompt pre-filled for this logo
      master.svg           # vector master (or designer-checked trace)
      source/              # original reference images
      CHANGELOG.md         # what changed vs previous version and who confirmed
    v2/ ...                # new version only on a confirmed change; v1 is never edited
```

## Lifecycle
1. Reference image attached → draft SPEC + flags (local only).
2. Human confirms flagged items.
3. Freeze → copy to `logos/<slug>/vN/`, commit, push, tag `logo-<slug>-vN`.
4. Edit requests → serve the frozen SPEC + pre-filled edit prompt; logo changes are SVG/code
   edits, scene/background work is generative with the logo masked, then composited and verified
   by code (Delta E ≤ 2, OCR wordmark match, SSIM on protected regions, bbox tolerance).

## Using from Claude
Point a Claude project at the raw files, e.g.
`https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/logos/<slug>/v1/SPEC.json`
or paste `SPEC.json` + `edit-prompt.md` into the project instructions.
The same files drive Grok, so both platforms work from one locked spec.
