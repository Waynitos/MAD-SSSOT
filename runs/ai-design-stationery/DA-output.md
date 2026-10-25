# DA — Devil's Advocate Position
# RMAD Run: ai-design-stationery
# Date: 2026-10-25

## Position
Claude-only HTML/CSS artifacts are a dead end for professional design work. The architecture is missing critical components: print pipeline, vector source files, font-licensing enforcement, and a bridge from GitHub tokens into proper design tools.

## Argument

Claude artifacts are web pages, not design assets, and conflating the two creates a workflow that looks productive but produces outputs that cannot travel. A flash card built as an HTML artifact looks correct on screen, but hand it to a printer and you have nothing — no bleed, no CMYK, no crop marks, no PDF/X-1a. Hand it to a developer as a "source file" and you have a self-contained HTML page, not a component library. Hand it to a designer for iteration and they have to reverse-engineer CSS into shapes. Every output Claude produces in this channel is a dead end for professional design work the moment it leaves the browser.

The typography precision problem the user named is real, and HTML/CSS actually has the same problem at the edges. CSS handles web typography competently, but it cannot do optical kerning pairs correctly across all renderers, cannot do baseline grid alignment with the rigour a designer expects, cannot handle print-specific type rules (tracking in points, not ems), and font rendering varies by OS and browser. What looks tight and deliberate in Chrome on Mac looks different in Windows Edge. That is not brand consistency — that is browser roulette.

The deeper issue is that GitHub-stored brand tokens only help if the downstream tool can read them. Claude can read `--pp-primary: #4B2FA0` and apply it to an artifact. Canva cannot. Illustrator's colour swatches cannot. A print bureau's template cannot. The brand tokens in PLU-branding-extended.md are only as useful as the number of tools that consume them — and right now that number is one (Claude). A proper brand kit lives in Figma (as shared styles and a published component library) AND as a brand style guide. Neither of those are GitHub markdown files.

The user's stated goal — pop-up flash cards that incorporate official colours, branding, and graphic design style — actually splits into two very different requirements that cannot both be solved by the same tool. Digital interactive components (quiz flash cards, pop-ups, web UI) suit HTML/CSS fine. Print stationery (letterheads, business cards, envelope designs as seen in the Grok mockups) absolutely do not. Building both in Claude means either the digital components are overengineered, or the print assets are fatally underspecified.

## Real Failure Modes of Claude-Only Approach

- **[CRITICAL] Print assets are unbuildable** — no CMYK, no bleed/trim/safe zones, no PDF/X output, no spot colour. Severity: blocks entire stationery workflow.
- **[HIGH] No source file** — every artifact is a rendered output, not an editable design source. Designer cannot open and adjust it. Severity: design iteration requires Claude every time, no independence.
- **[HIGH] Font licensing / embedding** — Bauhaus 93 is not a Google Font. Claude cannot embed or guarantee it renders correctly in artifacts across devices. Web fallback ≠ brand font. Severity: core wordmark font absent from all digital outputs.
- **[MEDIUM] Typography precision at fine scale** — CSS kerning, leading, and optical alignment are approximate. For anything someone is judging against a designer's eye, it will fall short. Severity: credibility risk for a design studio.
- **[MEDIUM] No component reuse** — each Claude artifact is a standalone page. There is no shared symbol: "update the button style and it propagates everywhere" does not exist. Severity: brand drift across artifacts over time.
- **[MEDIUM] Colour accuracy** — screen RGB ≠ print CMYK. `#4B2FA0` rendered on screen and Pantone 2685 C on a printed envelope are not the same. Severity: brand colour inconsistency across media.
- **[LOW] Token reach** — GitHub tokens only speak to Claude. Figma, Illustrator, Canva cannot read them without a bridge tool.

## What Actually Solves the Problem

**Figma + Tokens Studio plugin (digital brand system)**
Best-in-class for digital brand consistency. Tokens Studio reads GitHub-stored token files and pushes them into Figma styles automatically — THIS is the bridge that makes the GitHub SSSOT actually speak to a design tool. AI features in Figma generate layouts while respecting your component library. Exports to developer handoff (CSS values, React components).

**Adobe Illustrator + Firefly (logo + print)**
The only correct tool for the logo redesign brief and stationery work. Firefly AI generates vector-compatible concepts inside Illustrator, full typographic control, CMYK output, bleed/trim/safe zones, PDF/X export. This is what was built for the typography precision problem the user named.

**Canva Pro (fastest templated brand outputs)**
Brand Kit stores colours, fonts, and logos centrally — every template inherits them. For flash cards, social assets, and simple stationery mockups, this is lowest friction. Print export quality is adequate for most stationery, not for high-end production.

**Honest answer for this specific user:**
- Flash cards / digital UI components → Claude HTML artifacts (good fit, fast, inherits tokens)
- Logo redesign → Illustrator (non-negotiable for vector precision)
- Print stationery (letterhead, business cards, envelopes) → Illustrator or Canva Pro
- Brand component library for repeatable digital use → Figma with Tokens Studio reading from GitHub
