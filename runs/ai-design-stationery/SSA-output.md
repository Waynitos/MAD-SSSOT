# SSA — Synthesizer Verdict
# RMAD Run: ai-design-stationery
# Date: 2026-10-25

---

## Verdict Table

| Question | Winner | Verdict |
|----------|--------|---------|
| Claude artifacts for digital UI components (flash cards, quizzes, pop-ups)? | AA | ✅ YES — correct tool, deterministic typography, tokens apply directly |
| Claude artifacts for print stationery (letterhead, business cards, envelopes)? | DA | ❌ NO — no CMYK, no bleed, no print-ready export. Structural gap, not fixable |
| GitHub brand tokens as SSSOT? | AA | ✅ YES — but needs a bridge to reach Figma + Illustrator, not just Claude |
| AI image generators for branded text/layout outputs? | DA | ❌ NO — both agree here. AI image gen is illustration only, never layout/typography |
| Figma + Tokens Studio as the bridge? | DA | ✅ YES — this is the missing link. GitHub → Tokens Studio → Figma = live token sync |
| Best tool for logo redesign? | DA | ✅ Illustrator — vector, CMYK, precision. Non-negotiable |
| Best tool for quick templated brand outputs (social, cards)? | DA | ✅ Canva Pro with Brand Kit — lowest friction, adequate for most outputs |

---

## SSA Ruling: TWO TOOL CHAINS, ONE SSSOT

The DA wins on structural architecture. The AA wins on the digital component workflow.

These are not competing positions — they describe two different pipelines that share ONE source of truth (GitHub `PLU-branding-extended.md`). The error is trying to solve both with a single tool.

### Pipeline 1 — Digital Interactive (Claude-led)
**Use for:** Flash cards, quiz UIs, pop-up overlays, web components, any artifact viewed in a browser

```
PLU-branding-extended.md (GitHub)
  → Claude fetches tokens
    → Claude builds HTML/CSS artifact from stationery/phewphonics/ template
      → Published artifact: on-brand, deterministic typography, interactive
```

Token reach: instant. Brand consistency: structural (tokens are the source, not a reference). Typography precision: exact (CSS rules, not image generation).

### Pipeline 2 — Print & Vector (Figma/Illustrator-led)
**Use for:** Letterhead, business cards, envelopes, logo files, print-ready PDFs, Figma design handoff

```
PLU-branding-extended.md (GitHub)
  → Tokens Studio plugin (reads GitHub token file)
    → Figma styles updated automatically
      → Figma components / Illustrator swatches: always current
        → Print-ready PDF/X from Illustrator | Canva Pro for simpler jobs
```

Token reach: requires Tokens Studio setup once. After that: update GitHub → Figma auto-syncs.

---

## Win-Wins from Synthesis

**1. Stationery directive system in GitHub (implement now)**
Create `stationery/phewphonics/` in MAD-SSSOT with:
- HTML templates for digital components (Claude consumes these)
- `print-specs.md` — dimensions, bleed, CMYK equivalents, safe zones for print tools to consume
- `tokens.json` — Tokens Studio format (reads directly from PLU-branding-extended.md, machine-readable for Figma)

This means the SSSOT genuinely serves BOTH pipelines from one file.

**2. Figma Tokens Studio bridge (set up once, then automatic)**
- Install Tokens Studio plugin in Figma
- Point it at `stationery/phewphonics/tokens.json` in MAD-SSSOT repo
- Push token update to GitHub → Figma styles sync on next plugin run
- Cost: one afternoon to set up. Benefit: GitHub is now the real single source for both Claude AND Figma

**3. Claude handles digital, Canva Pro handles quick print, Illustrator handles precision print/logo**
Stop trying to use one tool for everything. Three tools, one source file that feeds them all.

**4. AI image generation — use it for illustration inside the container**
Midjourney / Firefly / DALL-E: generate background imagery, character illustrations, icons — things that go inside the branded layout. Never ask them to render text or control layout. Claude's HTML frame holds the brand; AI imagery fills the visual space inside it.

---

## Immediate Actions

### Priority 1 — Build `stationery/phewphonics/` in GitHub (this session)
```
stationery/phewphonics/
  README.md              ← directive guide + pipeline overview
  tokens.json            ← Tokens Studio format (machine-readable brand tokens)
  print-specs.md         ← CMYK, dimensions, bleed for every stationery item
  templates/
    flash-card.html      ← Bell quiz flash card template (ready to use now)
    popup-flash.html     ← Branded pop-up overlay
    stationery-header.html  ← Letterhead header block
    quiz-layout.html     ← Multi-card quiz wrapper
```

### Priority 2 — Tokens Studio bridge (Waynito to set up in Figma)
1. Install Tokens Studio plugin in Figma (free tier covers this)
2. Connect to GitHub repo: Waynitos/MAD-SSSOT
3. Point at `stationery/phewphonics/tokens.json`
4. Run sync — Figma styles now match GitHub tokens
5. Future: update PLU-branding-extended.md → push to GitHub → run Tokens Studio sync → Figma updates

### Priority 3 — Logo redesign brief (open, no timeline)
Tool: Adobe Illustrator with Firefly AI
Brief: BRAND-SOUL.md (already committed to GitHub)
Key direction: projection + precision, not volume/audio shorthand

---

## Tool Recommendation Summary

| Output type | Tool | Why |
|-------------|------|-----|
| Flash cards, quiz UIs, pop-ups | Claude HTML artifact | Deterministic, token-driven, interactive |
| Social graphics, quick stationery | Canva Pro + Brand Kit | Fastest, Brand Kit enforces colours/fonts |
| Letterhead, business cards, print stationery | Illustrator | CMYK, bleed, PDF/X, typography precision |
| Logo redesign | Illustrator + Firefly AI | Vector, CMYK, full precision |
| Design system component library | Figma + Tokens Studio | GitHub-synced tokens, developer handoff |
| Illustration / imagery (inside branded containers) | Midjourney / Firefly / DALL-E | Image gen for visuals only, never layout |
| Claude AI graphics "plugin" | Not applicable | Claude's strength is code artifacts, not image gen |

**Bottom line:** There is no single AI graphics tool that solves the typography precision problem across digital AND print. The correct answer is a two-pipeline system with GitHub as the SSSOT for both. Build the stationery directive structure in GitHub now — that is the lever that makes everything else automatic.
