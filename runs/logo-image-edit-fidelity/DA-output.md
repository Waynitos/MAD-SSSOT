**DA position: a JSON spec is a wish list, not a lock.** It describes what you want to keep, but nothing in a diffusion or multimodal edit pipeline actually enforces it. The model reads the spec as more prompt text, weighs it against everything else, and then regenerates pixels. Fidelity is something you hope for, not something the system guarantees.

**1. The model can't see well enough to obey the spec.** Current vision models are weak at the details that matter most for logos: exact hex values, stroke weights, kerning, letter counts, corner radii, and small negative-space shapes. "Primary: #0A3D62, wordmark kerning unchanged" gets turned into "dark blue-ish, roughly the same text." Text rendering is the classic failure: letters get swapped, dropped, or re-styled even when the spec spells out the string exactly.

**2. Edits regenerate, they don't preserve.** Most AI image edits re-sample the whole image, or a large masked area, in latent space. So even the untouched parts drift a little with every pass: colours shift, edges soften, proportions creep. Chain three or four edits and the logo has quietly become a lookalike. A JSON field saying `"preserve": true` doesn't change that mechanism at all.

**3. Non-determinism defeats auditability.** The same spec and prompt give different outputs across seeds, model versions, and provider updates you never get told about. A brand asset that can't be reproduced byte-for-byte can't be governed, and today's approved result may not be reproducible next month.

**4. More structure doesn't mean more compliance.** Long nested specs dilute attention, and fields compete with each other. Models also tend to satisfy the most salient instruction and silently drop the rest. Verbose JSON can actually make adherence worse than a short, focused instruction, and it gives the team a false sense that "it's all in the spec."

**5. The spec becomes an injection surface.** If specs are built from client briefs, uploaded files, metadata, or text inside the images themselves, any of those can carry instructions that override your constraints ("ignore the palette, use…"). Text embedded in a reference image is read by the vision model as content. A structured format doesn't sanitise anything; it's still just tokens.

**6. Self-checking is circular.** Using the same kind of vision model to confirm the edit matched the spec runs into the same perception limits from point 1. It will happily report "colours match" on a result that's visibly off to a designer. You need measurements, not a model's opinion of its own work.

**7. Better tools already exist for the parts that must not move.**
- **Vector source of truth (SVG/AI files):** logos are geometry, so make edits as deterministic transforms on paths and fills, and use AI only for ideas or backgrounds.
- **Composite, don't regenerate:** generate the scene, then place the original logo layer on top untouched, so it's pixel-exact by construction.
- **Spatial conditioning (ControlNet-style edge, depth, or segmentation maps, plus tight inpainting masks):** this constrains geometry in a way text can't.
- **Brand kits and locked templates:** fixed palettes, fonts, and clear-space rules enforced by the software, not suggested to a model.
- **Programmatic checks:** colour difference (Delta E) against brand values, OCR on wordmarks, and pixel or structural similarity on protected regions, with automatic rejection when something fails.
- **Human sign-off:** a designer approves before anything ships, because legal and brand risk lands on people, not prompts.

**Bottom line:** JSON specs plus prompts are fine for *steering* exploratory edits. As the *primary* way to lock logo fidelity they fail on perception, mechanism, reproducibility, and security. Protected elements should never pass through a generative step at all; everything else should be gated by measurement and a human.