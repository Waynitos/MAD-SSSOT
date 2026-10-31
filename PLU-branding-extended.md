# PLU-branding-extended.md
# Extended Brand DNA — Phewphonics 3D Design Studio
version: 1.2
last-updated: 2026-10-31
maintainer: Waynito (phewphonics@hotmail.com)

---

## How this file works

This file is the **Single Source of Truth for all brand DNA** used across Claude projects, apps, prompts, and UI components. When a session fetches PROJECT-LAUNCH-Plus.md, it can fetch this file on demand to get the full visual specification.

**Auto-inheritance rule:** Any project scaffolded via PLU-wizard.md inherits Global Defaults below. A named brand block (e.g. `## Phewphonics`) overrides only the tokens it specifies — all others fall through to Global Defaults.

---

## Global Defaults
*(Inherited by all projects unless a named brand block overrides)*

primary:        #1a1a1a
accent:         #2563eb
success:        #1a7a3c
warning:        #b07d00
danger:         #c0392b
bg-light:       #f8f7f4
bg-dark:        #141414
card:           #ffffff
card-dark:      #1e1e1e

font-body:      -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
font-mono:      "SF Mono", "Cascadia Code", monospace
font-display:   inherit

border-radius:  8px
spacing-unit:   8px
gutter:         16px

Buttons:        rounded-8px, accent fill, white text, hover darken 10%
Panels/cards:   1px border card-border, 8px radius, 16px padding

---

## Phewphonics — 3D Design Studio
*(Override block — paste into any project's BRANDING.md Overrides section to activate)*

brand:          Phewphonics 3D Design Studio
byline:         "SOUND BETTER?"
version:        1.2
last-updated:   2026-10-31
brand-soul:     https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/branding/phewphonics/BRAND-SOUL.md

### Colour Palette

primary:        #4B2FA0   /* Deep Brand Purple — main logo colour, CTA buttons, headings */
primary-dark:   #3A2280   /* Darker purple for hover states */
primary-light:  #6B4FC8   /* Lighter purple for highlights/links */
accent:         #7B5ED4   /* Mid-purple — active states, badges, tags */
bg-brand:       #4B2FA0   /* Solid purple background (envelope/card usage) */

rhema-blue:     #1A1A8C   /* Deep Rhema Blue — heavenly Word / precision accent (secondary to primary purple). RGB 26, 26, 140. From MAD run 2026-10-31. */

neutral-dark:   #333333   /* Near-black text, icons on light backgrounds */
neutral-mid:    #666666   /* Secondary text, captions */
neutral-light:  #CCCCCC   /* Borders, dividers */

bg-light:       #F5F5F7   /* Off-white page background */
bg-dark:        #1A1020   /* Deep purple-tinted dark mode background */
card:           #FFFFFF   /* Card/panel surface */
card-dark:      #2A1E40   /* Dark mode card — purple-tinted dark */

white:          #FFFFFF
text-on-dark:   #FFFFFF   /* Text on purple or dark backgrounds */
text-on-light:  #333333   /* Text on white/light backgrounds */

success:        #1a7a3c
warning:        #b07d00
danger:         #c0392b

### Typography

font-display:   "Bauhaus 93", "Nunito", "Varela Round", sans-serif
  /* Bauhaus 93 — confirmed wordmark font for "phewphonics" lettering.
     Not available on Google Fonts; use as installed system font or embed as woff2.
     Fallback: Nunito 700+800 (Google Fonts) for web use where Bauhaus 93 unavailable */

font-subtitle:  "Rajdhani", "Barlow Condensed", "Arial Narrow", sans-serif
  /* Tight spaced caps grotesque — matches "3D DESIGN STUDIO" subtitle treatment.
     Load via Google Fonts: Rajdhani weight 600+700 */

font-byline:    "Troglodyte Pop", "Trebuchet MS", sans-serif
  /* Confirmed byline font for "SOUND BETTER?" (and earlier geometric treatments such as "3D DESIGN SERVICES").
     Designer: Graham Meade / Apostrophic Labs (2001).
     Files typically: TROGLOP_.ttf (Pop) and TROGLO__.ttf (regular).
     Originally listed in source PDF as "Trogldyte" and substituted with Trebuchet MS when missing.
     Free display face — widely distributed; verify the included license file for commercial use before embedding or redistributing.
     Not on Google Fonts; install locally or self-host woff2 for web. */

font-body:      -apple-system, BlinkMacSystemFont, "Segoe UI", "Nunito", sans-serif
  /* Body copy — system stack with Nunito as fallback for brand consistency */

font-mono:      "SF Mono", "Cascadia Code", monospace

font-size-display:  clamp(2rem, 5vw, 4rem)
font-size-h1:       clamp(1.5rem, 3vw, 2.5rem)
font-size-h2:       1.5rem
font-size-body:     1rem
font-size-small:    0.875rem
font-size-subtitle: 0.75rem   /* for "3D DESIGN STUDIO"-style uppercase labels */
font-size-byline:   clamp(1.25rem, 3vw, 2rem)   /* for "SOUND BETTER?" */

letter-spacing-subtitle: 0.12em   /* Wide tracking for subtitle caps treatment */
text-transform-subtitle: uppercase

### Logo

logo-wordmark:          "phewphonics" lowercase — Bauhaus 93 font, outline/inline stroke style
logo-assets:            https://github.com/Waynitos/MAD-SSSOT/tree/main/branding/phewphonics/
logo-note:              Current mark (satellite dish / speaker icon) is earmarked for redesign —
                        it reads as consumer audio. Intent: project precision and outward transmission
                        without volume-symbol shorthand. See BRAND-SOUL.md for full brief.
logo-icon:              Satellite dish + shooting star — top-right of wordmark
logo-subtitle:          "3D DESIGN STUDIO" — spaced caps, below wordmark right-aligned
logo-byline:            "SOUND BETTER?" — Troglodyte Pop
logo-colour-primary:    #4B2FA0 on white bg
logo-colour-reversed:   #FFFFFF outline on #4B2FA0 bg (envelope/dark surface usage)
logo-colour-outline:    outline stroke version — #4B2FA0 stroke, white fill (standard usage)

logo-clear-space:       minimum 1x cap-height on all sides
logo-min-width:         120px digital / 30mm print

### Spacing & Layout

border-radius:      12px    /* Slightly more rounded than global default — matches logo style */
border-radius-sm:   6px
border-radius-pill: 999px

spacing-unit:   8px
gutter:         16px
gutter-lg:      24px
section-gap:    48px

### Component Specs

Buttons (primary):
  background: #4B2FA0
  color: #FFFFFF
  border-radius: 999px       /* Pill shape — matches brand's rounded aesthetic */
  padding: 10px 24px
  font: font-subtitle, 600, letter-spacing 0.08em, uppercase
  hover: background #3A2280

Buttons (secondary):
  background: transparent
  border: 2px solid #4B2FA0
  color: #4B2FA0
  border-radius: 999px
  hover: background #4B2FA0, color #FFFFFF

Panels/cards:
  background: #FFFFFF
  border: 1px solid #CCCCCC
  border-radius: 12px
  padding: 20px
  box-shadow: 0 2px 8px rgba(75,47,160,0.08)

Panels/cards (dark):
  background: #2A1E40
  border: 1px solid rgba(255,255,255,0.1)

Tags/badges:
  background: rgba(75,47,160,0.12)
  color: #4B2FA0
  border-radius: 999px
  font: font-subtitle, uppercase, 0.7rem, letter-spacing 0.1em

### Dark Mode

bg-dark:        #1A1020
card-dark:      #2A1E40
text-dark:      #FFFFFF
accent-dark:    #7B5ED4   /* Lighter purple for legibility on dark */
border-dark:    rgba(255,255,255,0.1)

### Google Fonts Import

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet">
```

### CSS Custom Properties (ready to paste)

```css
:root {
  --pp-primary:         #4B2FA0;
  --pp-primary-dark:    #3A2280;
  --pp-primary-light:   #6B4FC8;
  --pp-accent:          #7B5ED4;
  --pp-rhema-blue:      #1A1A8C;   /* Deep Rhema Blue — heavenly Word / precision accent. RGB 26, 26, 140. */
  --pp-white:           #FFFFFF;
  --pp-dark:            #333333;
  --pp-bg:              #F5F5F7;
  --pp-bg-dark:         #1A1020;
  --pp-card:            #FFFFFF;
  --pp-card-dark:       #2A1E40;

  --pp-font-display:    'Bauhaus 93', 'Nunito', 'Varela Round', sans-serif;
  --pp-font-subtitle:   'Rajdhani', 'Barlow Condensed', 'Arial Narrow', sans-serif;
  --pp-font-byline:     'Troglodyte Pop', 'Trebuchet MS', sans-serif;
  --pp-font-body:       -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Nunito', sans-serif;
  --pp-font-mono:       'SF Mono', 'Cascadia Code', monospace;

  --pp-radius:          12px;
  --pp-radius-sm:       6px;
  --pp-radius-pill:     999px;
  --pp-spacing:         8px;
  --pp-gutter:          16px;
  --pp-shadow:          0 2px 8px rgba(75,47,160,0.08);
}

@media (prefers-color-scheme: dark) {
  :root {
    --pp-bg:      #1A1020;
    --pp-card:    #2A1E40;
    --pp-dark:    #FFFFFF;
  }
}
```

---

## How to activate Phewphonics branding in a new project

In the project's `BRANDING.md` Overrides section, add:

```
## Active brand: Phewphonics 3D Design Studio
Fetch full spec: https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-branding-extended.md
Apply: ## Phewphonics block — all CSS custom properties and component specs
```

Claude will fetch this file at session start and apply the token set to all artifacts, apps, and UI outputs in that project.
