# Phewphonics — Print Stationery Specs
version: 1.0
last-updated: 2026-10-25
source-tokens: PLU-branding-extended.md

---

## CMYK / Colour for Print

| Token | Screen (RGB) | Print (CMYK) | Pantone |
|-------|-------------|--------------|---------|
| Primary brand purple | `#4B2FA0` | C:67 M:80 Y:0 K:0 | Pantone 2685 C |
| Primary dark (hover) | `#3A2280` | C:75 M:88 Y:0 K:5 | — |
| Accent | `#7B5ED4` | C:51 M:63 Y:0 K:0 | — |
| White | `#FFFFFF` | C:0 M:0 Y:0 K:0 | Paper white |
| Near-black | `#333333` | C:0 M:0 Y:0 K:80 | — |
| Rich black (large areas) | `#1A1A1A` | C:40 M:30 Y:30 K:100 | — |

> ⚠️ Always get a proof from your print bureau before a production run. CMYK values are approximations — actual output depends on press, paper, and ICC profile.

---

## Letterhead (A4)

```
Size:     210mm × 297mm (A4)
Bleed:    3mm all sides (live area: 204mm × 291mm)
Safe zone: 10mm from trim on all sides
Margin:   20mm top / 20mm sides / 25mm bottom

Layout:
  Top block (header):       Logo + "3D DESIGN STUDIO" subtitle + byline "SOUND BETTER?"
  Contact line (top right): email / web / phone — Rajdhani 10pt, neutral-mid colour
  Body area:                Left-aligned, Nunito body font, 11pt, 6mm line spacing
  Footer (bottom):          Thin 0.5pt rule, company details in 8pt Rajdhani spaced caps

Header dimensions:
  Logo mark:  45mm wide
  Logo top margin: 15mm from trim
  Logo left:  20mm from trim
  Header height: 35mm before body text begins

Colour option A (white ground): Logo solid purple on white | purple rule top
Colour option B (purple header): Logo reversed white on #4B2FA0 header band
```

**Export:** PDF/X-1a (press-ready) | CMYK | Embedded fonts | 300 DPI raster elements

---

## Business Card

```
Size:      90mm × 55mm (standard)
Bleed:     3mm all sides
Safe zone: 5mm from trim

Front (brand face):
  Background: #4B2FA0 (solid brand purple)
  Logo:       Reversed white — centre or upper-left
  Byline:     "SOUND BETTER?" — Rajdhani, white, 8pt, letter-spacing 0.1em
  No other text on front

Back (contact face):
  Background: White
  Name:       Bauhaus 93 (or Nunito 800 fallback), 12pt, #4B2FA0
  Title:      Rajdhani 600, 9pt, uppercase, letter-spacing 0.12em, #666666
  Contact:    Nunito 400, 9pt, #333333
  Web/email:  #4B2FA0, 9pt
  Logo mark:  Small (10mm) bottom-right corner, solid purple
```

**Export:** PDF/X-1a | CMYK | 300 DPI | Bleed on

---

## Envelope (DL — standard)

```
Size:      220mm × 110mm (DL)
Bleed:     3mm all sides
Safe zone: 6mm from trim

Layout:
  Left third:  Logo block — solid purple on white, or purple window band
  Window area: If windowed envelope, clear zone 93mm × 39mm, position 22mm from left, 14mm from bottom
  Return address (top-left): Rajdhani 8pt, spaced caps
  Seal flap (back): Optional brand purple band with "SOUND BETTER?" reverse type

Colour option A: Full white, purple logo top-left
Colour option B: Purple left-band (40mm wide) with reversed logo
```

---

## Compliments Slip (A5 landscape)

```
Size:      210mm × 148mm (A5 landscape) or 210mm × 99mm (DL slip)
Bleed:     3mm
Header:    Same as letterhead header block, scaled to A5
Body:      "With compliments" — Rajdhani 12pt, letter-spacing 0.12em, #4B2FA0
```

---

## Digital Preview Templates

For on-screen proofing and digital versions, use the HTML templates in `templates/`:
- `stationery-header.html` — letterhead header block at 96dpi
- These are NOT print-ready — for visual approval only, not for sending to a printer

---

## Logo Usage for Print

Raw files: `branding/phewphonics/` in MAD-SSSOT

| Usage | File | Notes |
|-------|------|-------|
| Colour on white | `logo-solid-purple.png` | Use EPS/AI master for print (request from designer) |
| Reversed on dark | `logo-outline-purple.png` | White reversed variant |
| B&W solid | `logo-solid-black.jpg` | Single-colour print, emboss, foil |
| B&W outline | `logo-outline-black.jpg` | Laser engraving, embossing outline |

> ⚠️ PNG/JPG files are reference quality. For production print, request vector EPS/AI files from the designer. PNG at 300 DPI minimum for digital print; vector for offset/litho.

---

## Fonts for Print

| Font | Weight | Use | Licence |
|------|--------|-----|---------|
| Bauhaus 93 | Regular | Wordmark only | Commercial licence required — do NOT use for body text in print |
| Rajdhani | 600, 700 | Subheadings, labels, spaced caps | Google Fonts (OFL) — free for all use |
| Nunito | 700, 800 | Headings, branded display | Google Fonts (OFL) — free for all use |
| Nunito | 400, 600 | Body text | Google Fonts (OFL) — free for all use |

> Embed all fonts in print-ready PDFs. Confirm with print bureau that PDF/X-1a requires fonts to be embedded (not just referenced).
