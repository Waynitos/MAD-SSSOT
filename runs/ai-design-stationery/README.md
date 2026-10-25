# RMAD Run: ai-design-stationery
Date: 2026-10-25
Topic: Best AI graphics tool for brand-consistent outputs + corporate stationery directive system in GitHub
Triggered by: Waynito (phewphonics@hotmail.com)

## SSA Verdict (short form)
**Two pipelines, one SSSOT.**
- Digital interactive (flash cards, pop-ups, quiz UIs) → Claude HTML artifacts from templates
- Print + vector (letterhead, business cards, logo) → Illustrator / Canva Pro / Figma + Tokens Studio
- No single AI image tool solves both — don't try to find one
- Tokens Studio is the bridge from GitHub tokens to Figma (set up once, then automatic)

## Files
- `AA-output.md` — Advocate: Claude artifacts are the right tool for digital components
- `DA-output.md` — Devil's Advocate: HTML artifacts fail for print; Figma/Illustrator are required; Tokens Studio is the missing bridge
- `SSA-output.md` — Synthesizer: full verdict table, two-pipeline architecture, tool recommendation matrix

## Immediate output
Created `stationery/phewphonics/`:
- `tokens.json` — Tokens Studio format (Figma bridge)
- `print-specs.md` — CMYK, bleed, dimensions for all stationery items
- `templates/flash-card.html` — flip card component (ready to use)
- `templates/popup-flash.html` — branded modal/overlay
- `templates/stationery-header.html` — letterhead header (digital preview)
- `README.md` — directive guide + pipeline overview

## Winner
DA on structural architecture (print gap, Tokens Studio bridge).
AA on digital component workflow (confirmed: HTML artifacts are correct for flash cards / quiz UI).
