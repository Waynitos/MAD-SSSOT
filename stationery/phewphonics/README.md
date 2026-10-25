# Phewphonics — Corporate Stationery Directives
version: 1.0
last-updated: 2026-10-25
source-tokens: PLU-branding-extended.md

---

## What This Folder Does

This folder is the **stationery directive system** for all Phewphonics branded outputs. It feeds TWO design pipelines from ONE source of truth (PLU-branding-extended.md + tokens.json):

```
PLU-branding-extended.md (GitHub SSSOT)
         │
         ├─→ tokens.json → Figma (via Tokens Studio plugin) → print-ready design assets
         │
         └─→ templates/*.html → Claude artifacts → digital interactive outputs
```

Any project with the bootstrap line can ask Claude to generate branded components. Claude fetches the relevant template, injects content, and publishes. The brand is already baked in — no per-project brand correction needed.

---

## Files

| File | What it is | Who uses it |
|------|-----------|-------------|
| `tokens.json` | Brand tokens in Tokens Studio format | Figma (via Tokens Studio plugin), future tooling |
| `print-specs.md` | CMYK, bleed, trim, safe zones, font specs for all stationery items | Illustrator / print bureau |
| `templates/flash-card.html` | Flip card component — quiz/language/BELL cards | Claude → artifact |
| `templates/popup-flash.html` | Branded modal/pop-up overlay | Claude → artifact |
| `templates/stationery-header.html` | Letterhead header block (digital preview) | Claude → approval preview |

---

## Directive: How Claude Uses These Templates

When a project session asks for a branded component (flash card, pop-up, stationery preview):

1. Claude fetches `PLU-branding-extended.md` → gets all CSS tokens
2. Claude fetches the relevant template from this folder
3. Claude injects the content variables (question/answer, title, contact details)
4. Claude publishes as a branded artifact

**Claude never designs from scratch for these output types. It fills the template.**

---

## Tokens Studio Setup (Figma bridge — one-time)

To connect GitHub tokens to Figma styles automatically:

1. Install [Tokens Studio for Figma](https://tokens.studio/) plugin (free tier works)
2. In the plugin: Settings → Sync → GitHub
3. Repository: `Waynitos/MAD-SSSOT`
4. File path: `stationery/phewphonics/tokens.json`
5. Branch: `main`
6. Click "Pull from GitHub" — Figma styles now match these tokens

**After any PLU-branding-extended.md colour/type update:**
- Push updated values to `tokens.json` in this folder
- Open Tokens Studio in Figma → Pull → styles sync automatically

---

## Pipeline Summary

| Output type | Tool | Source |
|-------------|------|--------|
| Flash cards, quiz UIs, pop-ups | Claude HTML artifact | `templates/*.html` + tokens |
| Social graphics, quick stationery | Canva Pro + Brand Kit | Use `print-specs.md` colours |
| Letterhead, business cards, envelopes (print-ready) | Adobe Illustrator | `print-specs.md` |
| Logo redesign | Adobe Illustrator + Firefly | `branding/phewphonics/BRAND-SOUL.md` |
| Design component library | Figma + Tokens Studio | `tokens.json` → GitHub sync |
| Background illustration / imagery | Midjourney / Firefly / DALL-E | For use INSIDE branded containers only |

---

## Template Variables Quick Reference

### flash-card.html
| Variable | Example |
|----------|---------|
| `{{CARD_TITLE}}` | BELL Language Quiz |
| `{{CARD_CATEGORY}}` | Vocabulary · Level 2 |
| `{{CARD_QUESTION}}` | What does "ephemeral" mean? |
| `{{CARD_HINT}}` | Think: temporary, fleeting |
| `{{CARD_ANSWER}}` | Lasting for a very short time |
| `{{CARD_NOTE}}` | From Greek "ephemeros" — lasting only a day |
| `{{CARD_NUMBER}}` | Card 3 of 12 |

### popup-flash.html
| Variable | Example |
|----------|---------|
| `{{POPUP_TITLE}}` | Ready to start? |
| `{{POPUP_BODY}}` | You'll see 12 vocabulary cards. Tap each to reveal the answer. |
| `{{POPUP_CTA}}` | Let's go |
| `{{POPUP_CANCEL}}` | Not yet |

### stationery-header.html
| Variable | Example |
|----------|---------|
| `{{CONTACT_NAME}}` | Waynito Surname |
| `{{CONTACT_EMAIL}}` | phewphonics@hotmail.com |
| `{{CONTACT_WEB}}` | phewphonics.com |
| `{{CONTACT_PHONE}}` | +61 4XX XXX XXX |
| `{{CONTACT_CITY}}` | Brisbane, Australia |
