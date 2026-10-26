# MAD PDF Layout Spec — Canonical Rules
version: 1.0
last-updated: 2026-10-26
status: LOCKED — do not change without testing all 6 pages

Hard-won through a painful iterative session. These rules are non-obvious.
**Read this before touching any margin, padding, or @page property.**

---

## The Core Problem (Why This Is Tricky)

Playwright renders PDFs on a dark background (`#1A1020`).

`@page { margin: Xmm }` creates whitespace **outside** the body — so the dark
background bleeds to the edge of the `@page` content area, but a white strip
appears beyond it. The result looks like zero margin because the dark bg hides it.

`body { padding: Xmm }` creates inset **inside** the body — but only works for
the first page. Subsequent pages after a `page-break-before` start fresh; they
inherit no top padding from the body element, so every page after the first
has no top gap.

---

## The Correct Solution (Locked In)

```
@page  { size: A4; margin: 0; }          ← ALWAYS 0. Never put margin here.
body   { padding: 0 14mm; }              ← Left/right only. Never top/bottom here.
.cover { padding-top: 16mm;              ← Cover page top gap
         padding-bottom: 16mm; }         ← Cover page bottom gap
.section { padding-top: 16mm;            ← Every section page top gap
           padding-bottom: 16mm; }       ← Every section page bottom gap
.page-break { page-break-before: always; } ← NO padding-top here — .section handles it
```

### Why it works
- `@page margin: 0` → dark background fills the full physical page edge-to-edge
- `body padding: 0 14mm` → consistent left/right breathing room on every page
- `.cover` and `.section` padding-top/bottom → visible inset on every page,
  applied to the element that starts the page, so it works on page 1 and all
  subsequent pages equally
- `.page-break` has NO extra padding → `.section`'s padding is the single
  source of truth; adding padding-top here too causes sections 2–5 to start
  lower than section 1

---

## Final Margin Values

| Edge   | Value | Set via               |
|--------|-------|-----------------------|
| Top    | 16mm  | `.cover` / `.section` padding-top  |
| Bottom | 16mm  | `.cover` / `.section` padding-bottom |
| Left   | 14mm  | `body` padding-left   |
| Right  | 14mm  | `body` padding-right  |

---

## Playwright Render Settings (Non-Negotiable)

```python
browser = await p.chromium.launch()
page = await browser.new_page()          # NO viewport override — causes clipping
await page.goto(f"file://{html_path}", wait_until="networkidle", timeout=30000)
await page.wait_for_timeout(2000)        # Let Google Fonts settle
await page.pdf(
    path=str(pdf_path),
    format="A4",
    print_background=True,              # REQUIRED — background colours won't render without this
    margin={"top":"0mm","bottom":"0mm","left":"0mm","right":"0mm"},  # ALWAYS 0 — CSS handles it
)
```

**Do NOT:**
- Set `viewport={"width": 794, "height": 1123}` — causes content clipping
- Set `margin` to anything other than 0mm — use CSS padding instead
- Use `@page { margin: Xmm }` for visual margins — it creates white strips

---

## Page Structure (HTML)

```html
<!-- Page 1: Cover -->
<div class="cover">
  ...cover content...
</div>

<!-- Page 2: Section 1 (flows after cover's page-break-after, NO page-break class) -->
<div class="section">
  ...section 1 content...
</div>

<!-- Pages 3–6: Sections 2–5 (each gets their own page) -->
<div class="section page-break">
  ...section content...
</div>
```

Section 1 has NO `page-break` class — it flows naturally onto page 2 after
the cover's `page-break-after: always`. Sections 2–5 each get `page-break`
which applies `page-break-before: always`.

---

## How a MAD Run Creates a PDF

`generate-mad-pdf.py` handles PDF generation automatically for every RMAD run:

1. **Prefers** `<run_folder>/print.html` — hand-crafted layout used as-is
2. **Falls back** to building HTML from `AA-output.md`, `DA-output.md`,
   `SSA-output.md` using `BASE_CSS` (which already has these rules baked in)

Run it:
```bash
python3 scripts/generate-mad-pdf.py runs/<topic>/
```

Output: `runs/<topic>/<slug>-MAD-Findings.pdf`

---

## Checklist Before Shipping a MAD PDF

- [ ] All 6 pages open with dark background bleeding to the edge (no white strips)
- [ ] Top margin consistent on page 1 (cover) and all subsequent pages
- [ ] Bottom margin consistent — content doesn't run to the edge
- [ ] Left/right margins equal and consistent across all pages
- [ ] Meta-pills on cover don't wrap (use `white-space: nowrap` + `font-size: 10px`)
- [ ] Page counter visible (top-right of each page)

---

## Files

| File | Purpose |
|------|---------|
| `scripts/generate-mad-pdf.py` | PDF generator — `BASE_CSS` has these rules baked in |
| `runs/<topic>/print.html` | Per-run hand-crafted layout — must follow these rules |
| `runs/<topic>/<slug>-MAD-Findings.pdf` | Final output committed alongside the run |

---

*This spec was locked after an extended debugging session on 2026-10-26.*
*The rules are non-obvious — trust the spec, not intuition.*
