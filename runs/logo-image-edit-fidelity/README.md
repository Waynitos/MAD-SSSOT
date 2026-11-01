# RMAD Cycle: Logo / Image Edit Fidelity Control

**Topic:** Best methods to capture technical details of an image layout or logo (font, size, spacing, colour, bounding boxes, etc.) so that AI-driven edits (Grok, Claude, Imagine) do not unintentionally alter protected design elements.

**Date:** 2026-11-02

**Agents:**
- AA-Logo-Edit-Fidelity (Advocate)
- DA-Logo-Edit-Fidelity (Devil's Advocate)
- SSA-Logo-Edit-Fidelity (Synthesiser)

## Summary of Verdict

The strongest practical approach combines a human-checked structured JSON technical specification (for description and measurement) with deterministic enforcement (SVG/vector masters, compositing of locked layers, programmatic verification via Delta E / OCR / SSIM, human sign-off). Generative models are restricted to unprotected content only.

JSON-in-prompt alone is insufficient for hard locks; it is useful for steering and as input to deterministic renderers/checkers.

See full outputs:
- [AA-output.md](AA-output.md)
- [DA-output.md](DA-output.md)
- [SSA-output.md](SSA-output.md)

## Next Steps Suggested
- Stand up a dedicated Extractor + Verifier bot/agent that produces and locks specs.
- Prefer SVG masters for logos.
- Adopt the short general edit prompt and extraction prompt from SSA-output.md as reusable templates.
- For Grok/Claude sessions, inject the frozen SPEC + protected-elements list at the start of every edit request.