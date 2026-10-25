# AA — Advocate Position
# RMAD Run: ai-design-stationery
# Date: 2026-10-25

## Position
Claude's HTML/CSS artifact system, driven by brand tokens stored in GitHub, is the correct primary tool for brand-consistent UI components (flash cards, pop-ups, quizzes) — NOT AI image generators. AI image tools are a complement for illustration/imagery only.

## Argument

HTML/CSS is not a workaround for the absence of a better design tool — it IS the correct tool for this job. Every pain point Waynito named (text alignment, kerning, typographic hierarchy) is a solved problem in CSS. `font-family: "Bauhaus 93"`, `letter-spacing: 0.12em`, `text-align: center`, `line-height: 1.4` — these are not approximations. They are exact. An AI image generator cannot guarantee pixel-accurate text placement because it is synthesising a rasterised prediction of what text looks like; Claude writing CSS is setting the actual rule. The output is structurally correct by definition, not statistically likely to look correct.

The GitHub token system already closes the brand-consistency gap before the component is even built. When Claude fetches `PLU-branding-extended.md`, it has `--pp-primary: #4B2FA0`, `--pp-font-display: 'Bauhaus 93'`, `--pp-radius-pill: 999px`, and the full component spec for buttons, cards, and badges. A flash card built from those tokens is not approximately on-brand — it is literally constructed from the same spec as every other output across every other project. No image AI has access to that file. No image AI could honour it even if it did.

A component library in GitHub — HTML/CSS templates for flash card, pop-up, stationery header, quiz layout — changes the workflow from "generate and correct" to "fill and ship." Instead of Claude reinventing a flash card from scratch and Waynito correcting the brand drift afterward, Claude pulls `templates/flash-card.html`, injects the content, and the brand is already there because the template was built from the tokens. This is how professional design systems work: Figma components, not fresh Figma files. The template IS the brand enforcement mechanism, and it lives in the SSSOT repo where it can be versioned, forked, and updated once to propagate everywhere.

AI image tools have one legitimate role: original illustration and photographic imagery that sits *inside* the branded container. A quiz flash card might have a generated illustration of a phonetics diagram or a language scene — that illustration lives in an `<img>` tag inside a Claude-built, brand-token-driven layout. The AI makes the picture; Claude controls the frame, the type, the colour, the spacing. This is the correct division of labour.

## Strongest Evidence

- CSS text rendering is deterministic — `font-size: 1.5rem; letter-spacing: 0.12em` produces the same result every time; DALL-E text generation does not
- Brand tokens are already in GitHub in CSS custom property format — zero transformation needed to apply them in an artifact
- Claude's artifact system supports dark mode, responsive layout, hover states, and interactivity — none of which any image generator can produce
- A template updated once in GitHub propagates to all future components built from it — image generators have no equivalent to a shared template
- Stationery (letterhead, business card layout, envelope) is a layout-and-typography problem, not an image problem — CSS handles it natively

## Proposed Architecture

**GitHub `MAD-SSSOT/stationery/phewphonics/`:**
```
templates/
  flash-card.html         ← quiz card: front/back flip, question/answer, brand tokens wired in
  popup-flash.html        ← branded modal/overlay component
  stationery-header.html  ← letterhead top section: logo + byline + contact block
  quiz-layout.html        ← multi-card quiz wrapper with score, progress, brand nav
  badge.html              ← small branded label/tag component
```

**Workflow for "give me a Bell language quiz flash card":**
1. User types it in any project with the bootstrap line
2. Claude fetches tokens + template → builds card with `#4B2FA0`, Bauhaus 93, pill buttons, correct spacing
3. User sees finished, on-brand card in ~10 seconds
4. If brand updates → update `PLU-branding-extended.md` → all future cards inherit it automatically
