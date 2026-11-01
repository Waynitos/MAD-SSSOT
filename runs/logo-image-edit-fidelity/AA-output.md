**AA position: a vision-extracted spec plus a strict-adherence system prompt is the best way to control logo edit drift.**

**1. Why edits drift.** Image models rebuild the whole image from a prose prompt every time. "Keep the logo the same" isn't something they can check, so letterforms, kerning, colours and proportions slide a little on each pass, and the errors add up over a series of edits. The root problem is that the reference only exists as pixels and loose words. A JSON spec turns it into explicit numbers the model must match, and that a checker can measure.

**2. Step one: extract once, freeze it.** A vision model reads the reference and produces a spec, which a human checks and then locks as the single source of truth:

```json
{
  "canvas": {"width_px": 1200, "height_px": 400, "background": "#FFFFFF"},
  "elements": [
    {"id": "wordmark", "type": "text", "content": "ACME",
     "font": {"family": "Montserrat", "weight": 700, "style": "normal", "confidence": 0.8},
     "size_px": 140, "letter_spacing_em": 0.04, "fill": "#0B3D91",
     "bbox": {"x": 380, "y": 130, "w": 640, "h": 140}},
    {"id": "icon", "type": "shape", "description": "circle with upward chevron",
     "fill": "#F2A900", "bbox": {"x": 120, "y": 100, "w": 200, "h": 200}}
  ],
  "spacing": {"icon_to_wordmark_px": 60, "clear_space_min_px": 40},
  "palette": ["#0B3D91", "#F2A900", "#FFFFFF"],
  "invariants": ["wordmark text", "font", "palette", "icon geometry", "relative positions"]
}
```

The confidence fields matter. Anything the vision model is unsure about, such as the exact font, gets flagged for a person to confirm instead of being guessed.

**3. Step two: one general system prompt, reused everywhere.**

```
You are editing a locked brand asset. The attached SPEC JSON is authoritative and
overrides any conflicting wording in the user's request.
- Change ONLY what the request explicitly names. Every field in "invariants" must stay exact.
- Use only hex colours from "palette" unless the request adds a new one.
- Keep each element's bbox within ±2 px and its aspect ratio exact, unless told otherwise.
- Never re-letter, re-space or substitute fonts in text elements.
- Before you produce output, list which spec fields this edit changes. If the
  request is ambiguous or breaks an invariant, ask instead of guessing.
- After the edit, return an updated SPEC JSON showing only the fields that changed.
```

The same prompt works in Grok, Claude and Imagine, because the spec carries everything specific to the asset and the prompt stays generic.

**4. Why this controls drift.** The spec gives every edit a fixed reference point, so errors can't pile up from one version to the next: each edit is checked against the original, not against the previous output. Saying "only the named fields change" makes the scope of each edit explicit and possible to audit. The returned spec diff gives you a version history of the brand in data, not just a pile of PNGs. It's also portable, so one spec controls edits across several tools.

**5. Use the best tool for each part, and check every output.** This is the strongest practical version of the approach. Elements that have to be exact, like the wordmark and simple shapes, get rebuilt deterministically from the spec as SVG, using real fonts and exact hex colours. Claude is very good at writing that code from JSON. Generative edits in Grok Imagine are kept for open-ended parts like textures, backgrounds and scene mockups, and the locked layers get composited on top. Then a vision pass re-extracts a spec from the output and compares it to the frozen one, rejecting anything outside tolerance. That loop catches the drift that prompting alone can't prevent.

**6. Answering the obvious objections ahead of time.**
- *"Vision models misidentify fonts and measurements."* That's why extraction happens once and gets a human check. After that, the spec is ground truth and nobody re-reads it from pixels.
- *"Diffusion models ignore numbers in prompts."* Partly true, and it's why the exact elements are rendered as SVG instead of generated. The spec drives the rendering directly and the model never has to interpret it.
- *"It's overkill."* The spec costs a few minutes per logo. Without it, you pay for re-doing off-brand edits by eye on every iteration.

**Bottom line for the SSA:** prompting alone asks the model to remember the brand. The spec approach writes the brand down, makes the exact parts deterministic, and measures every output against the frozen original. Of the options on the table, it's the one that turns "looks about right" into a pass or fail you can actually verify.