#!/usr/bin/env python3
"""
generate-mad-pdf.py
-------------------
Generate a PHONICSPlus-branded PDF from a completed MAD run.

Usage:
    python3 generate-mad-pdf.py <run_folder>

Example:
    python3 generate-mad-pdf.py runs/vault-cloud-migration

Reads:  <run_folder>/AA-output.md, DA-output.md, SSA-output.md, README.md
Writes: <run_folder>/<topic-slug>-MAD-Findings.pdf

Requirements:
    pip install playwright --break-system-packages
    playwright install chromium

The script builds a self-contained print-optimised HTML in /tmp,
renders it to A4 PDF via Playwright (background colours preserved),
and saves the PDF alongside the MAD run files.
"""

import asyncio
import re
import sys
import os
import textwrap
from pathlib import Path
from datetime import date

# ── Fallback PHONICSPlus tokens (used if PLU-branding-extended.md unavailable) ──
TOKENS = {
    "primary":   "#4B2FA0",
    "accent":    "#7B5ED4",
    "accent_hi": "#9B82E8",
    "bg":        "#1A1020",
    "bg_card":   "#231730",
    "bg_card2":  "#2C1D3E",
    "border":    "rgba(123,94,212,0.3)",
    "border_hi": "rgba(123,94,212,0.6)",
    "fg":        "#F0EAF8",
    "fg_sub":    "#C8B8E8",
    "fg_muted":  "#9A88B8",
    "go":        "#2ECC71",
    "go_bg":     "rgba(46,204,113,0.15)",
    "warn":      "#F39C12",
    "warn_bg":   "rgba(243,156,18,0.15)",
    "crit":      "#E74C3C",
    "crit_bg":   "rgba(231,76,60,0.15)",
    "sig":       "#E67E22",
    "sig_bg":    "rgba(230,126,34,0.15)",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800&family=Rajdhani:wght@600;700&family=Inter:wght@400;500;600&display=swap');

@page {{ size: A4; margin: 16mm 14mm; }}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --primary:   {primary};
  --accent:    {accent};
  --accent-hi: {accent_hi};
  --bg:        {bg};
  --bg-card:   {bg_card};
  --bg-card2:  {bg_card2};
  --border:    {border};
  --border-hi: {border_hi};
  --fg:        {fg};
  --fg-sub:    {fg_sub};
  --fg-muted:  {fg_muted};
  --go:        {go};
  --go-bg:     {go_bg};
  --warn:      {warn};
  --warn-bg:   {warn_bg};
  --crit:      {crit};
  --crit-bg:   {crit_bg};
  --sig:       {sig};
  --sig-bg:    {sig_bg};
  --font-disp: 'Nunito', Arial, sans-serif;
  --font-sub:  'Rajdhani', Arial, sans-serif;
  --font-body: 'Inter', Arial, sans-serif;
}}

html, body {{
  background: var(--bg); color: var(--fg);
  font-family: var(--font-body); font-size: 12.5px; line-height: 1.55;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}}

.wrap {{ width: 100%; }}

/* cover */
.cover {{
  page-break-after: always;
  padding-bottom: 28px;
  border-bottom: 2px solid var(--border);
}}
.cover-logo {{
  display: flex; align-items: center; gap: 10px; margin-bottom: 20px;
}}
.logo-badge {{
  width: 36px; height: 36px; border-radius: 999px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-disp); font-weight: 800; font-size: 14px; color: #fff;
}}
.logo-text {{
  font-family: var(--font-sub); font-weight: 700; font-size: 11px;
  letter-spacing: .1em; text-transform: uppercase; color: var(--fg-muted);
}}
.cover-eyebrow {{
  font-family: var(--font-sub); font-weight: 600; font-size: 11px;
  letter-spacing: .14em; text-transform: uppercase; color: var(--accent-hi);
  margin-bottom: 10px;
}}
.cover h1 {{
  font-family: var(--font-disp); font-weight: 800; font-size: 30px;
  line-height: 1.15; color: var(--fg); margin-bottom: 12px;
}}
.cover h1 span {{ color: var(--accent-hi); }}
.cover-sub {{ color: var(--fg-sub); font-size: 13px; margin-bottom: 18px; }}
.verdict-chip {{
  display: inline-flex; align-items: center; gap: 7px;
  padding: 6px 16px; border-radius: 999px;
  font-family: var(--font-sub); font-weight: 700; font-size: 12px;
  letter-spacing: .07em; text-transform: uppercase;
  background: var(--go-bg); border: 1.5px solid var(--go); color: var(--go);
}}
.verdict-chip::before {{
  content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--go);
}}
.meta-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px; }}
.meta-pill {{
  font-family: var(--font-sub); font-weight: 600; font-size: 10px;
  letter-spacing: .06em; text-transform: uppercase;
  color: var(--fg-muted); border: 1px solid var(--border);
  border-radius: 999px; padding: 2px 10px;
}}

/* sections */
.section {{ margin-bottom: 28px; }}
.section-eyebrow {{
  font-family: var(--font-sub); font-weight: 600; font-size: 10px;
  letter-spacing: .14em; text-transform: uppercase; color: var(--accent-hi);
  margin-bottom: 5px;
}}
.section-title {{
  font-family: var(--font-disp); font-weight: 800; font-size: 19px;
  color: var(--fg); padding-bottom: 9px; border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}}
.section-sub {{ color: var(--fg-muted); font-size: 11.5px; margin-bottom: 16px; margin-top: 4px; }}

/* markdown prose */
.prose h2 {{
  font-family: var(--font-disp); font-weight: 800; font-size: 15px;
  color: var(--fg); margin: 18px 0 8px;
}}
.prose h3 {{
  font-family: var(--font-sub); font-weight: 700; font-size: 13px;
  color: var(--accent-hi); margin: 14px 0 6px;
}}
.prose p {{ color: var(--fg-sub); font-size: 12px; margin-bottom: 8px; line-height: 1.6; }}
.prose ul, .prose ol {{ color: var(--fg-sub); font-size: 12px; padding-left: 20px; margin-bottom: 10px; }}
.prose li {{ margin-bottom: 4px; line-height: 1.55; }}
.prose strong {{ color: var(--fg); font-weight: 600; }}
.prose table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; margin-bottom: 12px; }}
.prose thead tr {{ background: var(--bg-card2); }}
.prose th {{
  padding: 8px 11px; text-align: left;
  font-family: var(--font-sub); font-weight: 700; font-size: 10px;
  letter-spacing: .1em; text-transform: uppercase; color: var(--fg-muted);
}}
.prose td {{
  padding: 8px 11px; border-top: 1px solid var(--border);
  color: var(--fg-sub); vertical-align: top;
}}
.prose blockquote {{
  border-left: 3px solid var(--accent); padding-left: 12px;
  color: var(--fg-muted); font-size: 12px; margin: 10px 0;
}}
.prose hr {{ border: none; border-top: 1px solid var(--border); margin: 16px 0; }}

.page-break {{ page-break-before: always; padding-top: 24px; }}
.no-break {{ page-break-inside: avoid; }}

/* footer */
.doc-footer {{
  margin-top: 32px; padding-top: 14px;
  border-top: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
  font-family: var(--font-sub); font-weight: 600; font-size: 10px;
  letter-spacing: .06em; text-transform: uppercase; color: var(--fg-muted);
}}
""".format(**TOKENS)


def md_to_html(md: str) -> str:
    """Very lightweight Markdown → HTML for the prose sections."""
    lines = md.split('\n')
    html_parts = []
    in_table = False
    in_ul = False
    in_ol = False

    def close_list():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append('</ul>')
            in_ul = False
        if in_ol:
            html_parts.append('</ol>')
            in_ol = False

    def inline(s):
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
        s = re.sub(r'`(.+?)`', r'<code style="font-size:11px;color:var(--accent-hi)">\1</code>', s)
        return s

    for line in lines:
        # headings
        if line.startswith('### '):
            close_list()
            html_parts.append(f'<h3>{inline(line[4:])}</h3>')
        elif line.startswith('## '):
            close_list()
            html_parts.append(f'<h2>{inline(line[3:])}</h2>')
        elif line.startswith('# '):
            close_list()
            html_parts.append(f'<h2>{inline(line[2:])}</h2>')
        # hr
        elif re.match(r'^---+$', line.strip()):
            close_list()
            html_parts.append('<hr>')
        # table
        elif line.startswith('|'):
            if not in_table:
                html_parts.append('<table><thead><tr>')
                cells = [c.strip() for c in line.strip('|').split('|')]
                for c in cells:
                    html_parts.append(f'<th>{inline(c)}</th>')
                html_parts.append('</tr></thead><tbody>')
                in_table = True
            elif re.match(r'^\|[-| :]+\|$', line.strip()):
                pass  # separator row
            else:
                cells = [c.strip() for c in line.strip('|').split('|')]
                html_parts.append('<tr>')
                for c in cells:
                    html_parts.append(f'<td>{inline(c)}</td>')
                html_parts.append('</tr>')
        else:
            if in_table:
                html_parts.append('</tbody></table>')
                in_table = False
            # unordered list
            if re.match(r'^[-*] ', line):
                if not in_ul:
                    close_list()
                    html_parts.append('<ul>')
                    in_ul = True
                html_parts.append(f'<li>{inline(line[2:])}</li>')
            # ordered list
            elif re.match(r'^\d+\. ', line):
                if not in_ol:
                    close_list()
                    html_parts.append('<ol>')
                    in_ol = True
                html_parts.append(f'<li>{inline(re.sub(r"^\d+\. ", "", line))}</li>')
            elif line.strip() == '':
                close_list()
            else:
                close_list()
                if line.strip():
                    html_parts.append(f'<p>{inline(line)}</p>')

    close_list()
    if in_table:
        html_parts.append('</tbody></table>')

    return '\n'.join(html_parts)


def build_html(run_dir: Path, topic_title: str) -> str:
    """Build print-optimised HTML from MAD run files."""

    def read(name):
        p = run_dir / name
        return p.read_text(encoding='utf-8') if p.exists() else f"_{name} not found_"

    aa  = read('AA-output.md')
    da  = read('DA-output.md')
    ssa = read('SSA-output.md')

    # Extract verdict line from SSA for cover chip
    verdict = "Conditional Go"
    m = re.search(r'VERDICT:\s*(.+)', ssa, re.IGNORECASE)
    if m:
        verdict = m.group(1).strip()

    today = date.today().strftime('%B %Y')
    slug  = run_dir.name

    cover_title_parts = topic_title.split(' — ', 1)
    if len(cover_title_parts) == 2:
        cover_h1 = f"{cover_title_parts[0]}<br><span>{cover_title_parts[1]}</span>"
    else:
        cover_h1 = topic_title

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{topic_title} — MAD Findings</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

<!-- COVER -->
<div class="cover">
  <div class="cover-logo">
    <div class="logo-badge">PH</div>
    <span class="logo-text">Phewphonics · MAD Framework</span>
  </div>
  <div class="cover-eyebrow">MAD Run — {today} · AA · DA · SSA</div>
  <h1>{cover_h1}</h1>
  <p class="cover-sub">Full Multi-Agent Debate output: Advocate (AA), Devil's Advocate (DA), and Synthesiser (SSA) verdict. Generated by the MAD Framework from runs/{slug}/.</p>
  <div class="verdict-chip">{verdict}</div>
  <div class="meta-row">
    <span class="meta-pill">MAD Framework</span>
    <span class="meta-pill">AA · DA · SSA</span>
    <span class="meta-pill">{today}</span>
    <span class="meta-pill">{slug}</span>
  </div>
</div>

<!-- SSA VERDICT -->
<div class="section">
  <div class="section-eyebrow">Synthesiser Verdict</div>
  <div class="section-title">SSA Output — Final Verdict</div>
  <div class="section-sub">Synthesised from full AA and DA debate. This is the actionable output.</div>
  <div class="prose">{md_to_html(ssa)}</div>
</div>

<!-- AA OUTPUT -->
<div class="section page-break">
  <div class="section-eyebrow">Advocate Agent</div>
  <div class="section-title">AA Output — Strongest Case FOR</div>
  <div class="section-sub">Full advocate position. All arguments for proceeding.</div>
  <div class="prose">{md_to_html(aa)}</div>
</div>

<!-- DA OUTPUT -->
<div class="section page-break">
  <div class="section-eyebrow">Devil's Advocate Agent</div>
  <div class="section-title">DA Output — Strongest Case AGAINST</div>
  <div class="section-sub">Full devil's advocate position. All failure modes and risks.</div>
  <div class="prose">{md_to_html(da)}</div>
</div>

<!-- FOOTER -->
<div class="doc-footer">
  <span>Phewphonics MAD Framework</span>
  <span>{topic_title}</span>
  <span>{today}</span>
</div>

</div>
</body>
</html>"""


async def render_pdf(html_path: Path, pdf_path: Path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{html_path}", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
        )
        await browser.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-mad-pdf.py <run_folder>")
        print("Example: python3 generate-mad-pdf.py runs/vault-cloud-migration")
        sys.exit(1)

    run_dir = Path(sys.argv[1])
    if not run_dir.exists():
        print(f"ERROR: Run folder not found: {run_dir}")
        sys.exit(1)

    # Derive title from README or folder name
    readme = run_dir / 'README.md'
    topic_title = run_dir.name.replace('-', ' ').title()
    if readme.exists():
        m = re.search(r'^#\s+MAD Run:\s*(.+)', readme.read_text(), re.MULTILINE)
        if m:
            topic_title = m.group(1).strip()

    slug = re.sub(r'[^a-z0-9]+', '-', topic_title.lower()).strip('-')
    pdf_name = f"{slug}-MAD-Findings.pdf"
    html_tmp = Path(f"/tmp/mad-print-{slug}.html")
    pdf_out  = run_dir / pdf_name

    print(f"Topic  : {topic_title}")
    print(f"Run dir: {run_dir}")
    print(f"PDF out: {pdf_out}")
    print("Building HTML…")

    html = build_html(run_dir, topic_title)
    html_tmp.write_text(html, encoding='utf-8')
    print(f"HTML written to {html_tmp} ({len(html):,} chars)")

    print("Rendering PDF via Playwright…")
    asyncio.run(render_pdf(html_tmp, pdf_out))

    size = pdf_out.stat().st_size
    print(f"PDF written: {pdf_out} ({size:,} bytes) ✅")
    html_tmp.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
