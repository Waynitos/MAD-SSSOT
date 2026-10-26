#!/usr/bin/env python3
"""
generate-mad-pdf.py
-------------------
Generate a PHONICSPlus-branded, fully-designed PDF from a completed MAD run.

Usage:
    python3 generate-mad-pdf.py <run_folder>

Example:
    python3 generate-mad-pdf.py runs/vault-cloud-migration

Prefers:  <run_folder>/print.html  (hand-crafted layout — used as-is)
Fallback: Reads AA-output.md, DA-output.md, SSA-output.md and builds a
          structured branded layout with verdict banner, stat tiles, cards.

Writes: <run_folder>/<slug>-MAD-Findings.pdf

Requirements:
    pip install playwright --break-system-packages
    playwright install chromium
"""

import asyncio, re, sys, os
from pathlib import Path
from datetime import date

# ── PHONICSPlus fallback tokens ──────────────────────────────────────────────
T = {
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

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800&family=Rajdhani:wght@600;700&family=Inter:wght@400;500;600&display=swap');

@page {{ size: A4; margin: 0; }}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --primary:{primary}; --accent:{accent}; --accent-hi:{accent_hi};
  --bg:{bg}; --bg-card:{bg_card}; --bg-card2:{bg_card2};
  --border:{border}; --border-hi:{border_hi};
  --fg:{fg}; --fg-sub:{fg_sub}; --fg-muted:{fg_muted};
  --go:{go}; --go-bg:{go_bg};
  --warn:{warn}; --warn-bg:{warn_bg};
  --crit:{crit}; --crit-bg:{crit_bg};
  --sig:{sig}; --sig-bg:{sig_bg};
  --font-disp:'Nunito',Arial,sans-serif;
  --font-sub:'Rajdhani',Arial,sans-serif;
  --font-body:'Inter',Arial,sans-serif;
}}

html,body {{
  background:var(--bg); color:var(--fg);
  font-family:var(--font-body); font-size:12.5px; line-height:1.55;
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
  padding: 0 14mm;
}}
.wrap {{ width:100%; }}

/* ── cover ── */
/* MARGIN RULE: @page margin must be 0 so dark bg fills edge-to-edge.
   Top/bottom inset via padding on .cover and .section. Left/right via body padding. */
.cover {{ page-break-after:always; padding-top:16mm; padding-bottom:16mm; border-bottom:2px solid var(--border); }}
.cover-logo {{ display:flex; align-items:center; gap:10px; margin-bottom:20px; }}
.logo-badge {{
  width:36px;height:36px;border-radius:999px;
  background:linear-gradient(135deg,var(--primary),var(--accent));
  display:flex;align-items:center;justify-content:center;
  font-family:var(--font-disp);font-weight:800;font-size:14px;color:#fff;
}}
.logo-text {{ font-family:var(--font-sub);font-weight:700;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--fg-muted); }}
.cover-eyebrow {{ font-family:var(--font-sub);font-weight:600;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-hi);margin-bottom:10px; }}
.cover h1 {{ font-family:var(--font-disp);font-weight:800;font-size:30px;line-height:1.15;color:var(--fg);margin-bottom:12px; }}
.cover h1 span {{ color:var(--accent-hi); }}
.cover-sub {{ color:var(--fg-sub);font-size:13px;margin-bottom:18px; }}
.verdict-chip {{
  display:inline-flex;align-items:center;gap:7px;padding:6px 16px;border-radius:999px;
  font-family:var(--font-sub);font-weight:700;font-size:12px;letter-spacing:.07em;text-transform:uppercase;
  background:var(--go-bg);border:1.5px solid var(--go);color:var(--go);
}}
.verdict-chip::before {{ content:"";width:7px;height:7px;border-radius:50%;background:var(--go); }}
.meta-row {{ display:flex;gap:8px;flex-wrap:wrap;margin-top:14px; }}
.meta-pill {{
  font-family:var(--font-sub);font-weight:600;font-size:10px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--fg-muted);border:1px solid var(--border);border-radius:999px;padding:2px 10px;
}}

/* ── section ── */
.section {{ margin-bottom:28px; padding-top:16mm; padding-bottom:16mm; }}
.page-break {{ page-break-before:always; }}
.no-break {{ page-break-inside:avoid; }}
.section-eyebrow {{ font-family:var(--font-sub);font-weight:600;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-hi);margin-bottom:5px; }}
.section-title {{ font-family:var(--font-disp);font-weight:800;font-size:19px;color:var(--fg);padding-bottom:9px;border-bottom:1px solid var(--border);margin-bottom:4px; }}
.section-sub {{ color:var(--fg-muted);font-size:11.5px;margin-bottom:16px;margin-top:4px; }}

/* ── verdict banner ── */
.verdict-banner {{
  background:linear-gradient(135deg,rgba(75,47,160,.35),rgba(123,94,212,.18));
  border:1.5px solid var(--border-hi);border-radius:14px;padding:22px;margin-bottom:20px;
}}
.verdict-label {{ font-family:var(--font-sub);font-weight:700;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--go);margin-bottom:7px; }}
.verdict-title {{ font-family:var(--font-disp);font-weight:800;font-size:20px;color:var(--fg);margin-bottom:9px; }}
.verdict-body {{ color:var(--fg-sub);font-size:12.5px;line-height:1.6; }}

/* ── stat tiles ── */
.stat-row {{ display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px; }}
.stat-tile {{ background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center; }}
.stat-num {{ font-family:var(--font-disp);font-weight:800;font-size:30px;line-height:1;margin-bottom:4px; }}
.stat-lbl {{ font-family:var(--font-sub);font-weight:600;font-size:10px;letter-spacing:.08em;text-transform:uppercase; }}

/* ── agree items ── */
.agree-list {{ display:flex;flex-direction:column;gap:8px;margin-bottom:18px; }}
.agree-item {{
  background:var(--bg-card);border:1px solid var(--border);border-radius:8px;
  padding:10px 13px;display:flex;gap:10px;align-items:flex-start;font-size:12px;
}}
.agree-icon {{ font-weight:700;flex-shrink:0;margin-top:1px; }}
.agree-item strong {{ color:var(--fg);font-weight:600; }}
.agree-item span {{ color:var(--fg-sub); }}

/* ── tables ── */
.table-wrap {{ overflow:hidden;border-radius:10px;border:1px solid var(--border);margin-bottom:12px; }}
table {{ width:100%;border-collapse:collapse;font-size:12px; }}
thead tr {{ background:var(--bg-card2); }}
th {{ padding:9px 12px;text-align:left;font-family:var(--font-sub);font-weight:700;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--fg-muted);white-space:nowrap; }}
td {{ padding:9px 12px;border-top:1px solid var(--border);color:var(--fg-sub);vertical-align:top; }}
.badge {{ display:inline-block;padding:2px 8px;border-radius:999px;font-family:var(--font-sub);font-weight:700;font-size:10px;letter-spacing:.05em;text-transform:uppercase;white-space:nowrap; }}
.crit {{ background:var(--crit-bg);color:var(--crit);border:1px solid rgba(231,76,60,.35); }}
.sig  {{ background:var(--sig-bg); color:var(--sig); border:1px solid rgba(230,126,34,.35); }}

/* ── condition cards ── */
.cond-grid {{ display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:18px; }}
.cond-card {{ background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:14px;display:flex;gap:11px;align-items:flex-start; }}
.cond-num {{
  width:26px;height:26px;border-radius:999px;
  background:linear-gradient(135deg,var(--primary),var(--accent));
  display:flex;align-items:center;justify-content:center;
  font-family:var(--font-disp);font-weight:800;font-size:12px;color:#fff;flex-shrink:0;
}}
.cond-title {{ font-family:var(--font-sub);font-weight:700;font-size:13px;color:var(--fg);margin-bottom:4px; }}
.cond-body {{ font-size:11.5px;color:var(--fg-muted);line-height:1.5; }}

/* ── sequence ── */
.seq {{ display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-bottom:20px; }}
.seq-step {{ background:var(--bg-card);border:1px solid var(--border);border-right:none;padding:14px 12px;position:relative; }}
.seq-step:first-child {{ border-radius:10px 0 0 10px; }}
.seq-step:last-child  {{ border-right:1px solid var(--border);border-radius:0 10px 10px 0; }}
.seq-arrow {{
  position:absolute;right:-12px;top:50%;transform:translateY(-50%);
  width:24px;height:24px;background:var(--bg);border:1px solid var(--border-hi);
  border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-size:10px;color:var(--accent-hi);z-index:2;
}}
.seq-step:last-child .seq-arrow {{ display:none; }}
.seq-label {{ font-family:var(--font-sub);font-weight:700;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--fg-muted);margin-bottom:4px; }}
.seq-app {{ font-family:var(--font-disp);font-weight:800;font-size:15px;color:var(--fg);margin-bottom:4px; }}
.seq-note {{ font-size:11px;color:var(--fg-muted);line-height:1.4; }}

/* ── triggers ── */
.trigger-list {{ display:flex;flex-direction:column;gap:8px;margin-bottom:18px; }}
.trigger-item {{
  display:flex;gap:10px;align-items:flex-start;
  background:var(--bg-card);border:1px solid var(--border);border-left:3px solid var(--crit);
  border-radius:0 8px 8px 0;padding:11px;
}}
.trigger-icon {{
  width:20px;height:20px;border-radius:50%;background:var(--crit-bg);
  display:flex;align-items:center;justify-content:center;
  font-size:10px;flex-shrink:0;color:var(--crit);font-weight:700;
}}
.trigger-text {{ font-size:12px;color:var(--fg-sub);line-height:1.5; }}
.trigger-text strong {{ color:var(--fg);font-weight:600; }}

/* ── test cards ── */
.test-grid {{ display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:18px; }}
.test-card {{ background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:13px; }}
.test-top {{ display:flex;gap:8px;align-items:center;margin-bottom:6px; }}
.test-num {{ font-family:var(--font-disp);font-weight:800;font-size:20px;color:var(--accent);line-height:1; }}
.test-title {{ font-family:var(--font-sub);font-weight:700;font-size:13px;color:var(--fg);margin-bottom:4px; }}
.test-body {{ font-size:11.5px;color:var(--fg-muted);line-height:1.5; }}

/* ── prose fallback (AA/DA sections) ── */
.prose h2 {{ font-family:var(--font-disp);font-weight:800;font-size:15px;color:var(--fg);margin:16px 0 7px; }}
.prose h3 {{ font-family:var(--font-sub);font-weight:700;font-size:13px;color:var(--accent-hi);margin:13px 0 5px; }}
.prose p  {{ color:var(--fg-sub);font-size:12px;margin-bottom:8px;line-height:1.6; }}
.prose ul,.prose ol {{ color:var(--fg-sub);font-size:12px;padding-left:18px;margin-bottom:10px; }}
.prose li {{ margin-bottom:4px;line-height:1.55; }}
.prose strong {{ color:var(--fg);font-weight:600; }}
.prose blockquote {{ border-left:3px solid var(--accent);padding-left:11px;color:var(--fg-muted);font-size:12px;margin:10px 0; }}
.prose hr {{ border:none;border-top:1px solid var(--border);margin:14px 0; }}
.prose table {{ width:100%;border-collapse:collapse;font-size:11.5px;margin-bottom:12px; }}
.prose thead tr {{ background:var(--bg-card2); }}
.prose th {{ padding:8px 11px;text-align:left;font-family:var(--font-sub);font-weight:700;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--fg-muted); }}
.prose td {{ padding:8px 11px;border-top:1px solid var(--border);color:var(--fg-sub);vertical-align:top; }}

/* ── footer ── */
.doc-footer {{
  margin-top:30px;padding-top:13px;border-top:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center;
  font-family:var(--font-sub);font-weight:600;font-size:10px;
  letter-spacing:.06em;text-transform:uppercase;color:var(--fg-muted);
}}
""".format(**T)


# ── lightweight markdown → html ──────────────────────────────────────────────
def inline(s):
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', s)
    s = re.sub(r'`(.+?)`', r'<code style="font-size:11px;color:var(--accent-hi)">\1</code>', s)
    return s

def md2html(md):
    out, in_table, in_ul, in_ol = [], False, False, False

    def close_list():
        nonlocal in_ul, in_ol
        if in_ul:  out.append('</ul>');  in_ul = False
        if in_ol:  out.append('</ol>');  in_ol = False

    for line in md.split('\n'):
        if line.startswith('### '):
            close_list(); out.append(f'<h3>{inline(line[4:])}</h3>')
        elif line.startswith('## '):
            close_list(); out.append(f'<h2>{inline(line[3:])}</h2>')
        elif line.startswith('# '):
            close_list(); out.append(f'<h2>{inline(line[2:])}</h2>')
        elif re.match(r'^---+$', line.strip()):
            close_list(); out.append('<hr>')
        elif line.startswith('|'):
            if not in_table:
                out.append('<table><thead><tr>')
                for c in [x.strip() for x in line.strip('|').split('|')]:
                    out.append(f'<th>{inline(c)}</th>')
                out.append('</tr></thead><tbody>')
                in_table = True
            elif re.match(r'^\|[-| :]+\|$', line.strip()):
                pass
            else:
                out.append('<tr>')
                for c in [x.strip() for x in line.strip('|').split('|')]:
                    out.append(f'<td>{inline(c)}</td>')
                out.append('</tr>')
        else:
            if in_table:
                out.append('</tbody></table>'); in_table = False
            if re.match(r'^[-*] ', line):
                if not in_ul: close_list(); out.append('<ul>'); in_ul = True
                out.append(f'<li>{inline(line[2:])}</li>')
            elif re.match(r'^\d+\. ', line):
                if not in_ol: close_list(); out.append('<ol>'); in_ol = True
                out.append(f'<li>{inline(re.sub(r"^\d+\. ","",line))}</li>')
            elif line.strip() == '':
                close_list()
            else:
                close_list()
                if line.strip(): out.append(f'<p>{inline(line)}</p>')

    close_list()
    if in_table: out.append('</tbody></table>')
    return '\n'.join(out)


# ── SSA structured extractor ─────────────────────────────────────────────────
def extract_ssa(ssa_md):
    """Pull key structured pieces from SSA-output.md for designed layout."""

    def section(header, text):
        m = re.search(rf'##\s+{re.escape(header)}\s*\n(.*?)(?=\n##|\Z)', text, re.S | re.I)
        return m.group(1).strip() if m else ''

    verdict_line = ''
    m = re.search(r'VERDICT:\s*(.+)', ssa_md, re.I)
    if m: verdict_line = m.group(1).strip()

    # Extract conditions (numbered sections)
    conditions = re.findall(
        r'###\s+CONDITION\s+(\d+)[:\s]+(.+?)\n\*\*What:\*\*\s*(.+?)(?=###\s+CONDITION|\Z)',
        ssa_md, re.S
    )

    # Extract rollback triggers from table rows
    triggers = re.findall(r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', ssa_md)
    triggers = [(a.strip(), b.strip()) for a, b in triggers
                if a not in ('Trigger', '---', 'Point', 'Question', 'Risk', 'Test')
                and len(a) > 5]

    # Extract test scenarios
    tests = re.findall(r'\d+\.\s+\*\*(.+?)\*\*[:\s]*(.+?)(?=\n\d+\.|\Z)', ssa_md, re.S)

    return verdict_line, conditions[:6], triggers[:6], tests[:8]


# ── build structured HTML (for runs without a print.html) ────────────────────
def build_html(run_dir, topic_title):
    def read(name):
        p = run_dir / name
        return p.read_text(encoding='utf-8') if p.exists() else ''

    aa_md  = read('AA-output.md')
    da_md  = read('DA-output.md')
    ssa_md = read('SSA-output.md')

    verdict_line, conditions, triggers, tests = extract_ssa(ssa_md)
    if not verdict_line: verdict_line = 'Conditional Go'

    today = date.today().strftime('%B %Y')
    slug  = run_dir.name

    parts = topic_title.split(' — ', 1)
    h1 = f"{parts[0]}<br><span>{parts[1]}</span>" if len(parts) == 2 else topic_title

    # ── conditions HTML ──
    cond_html = '<div class="cond-grid no-break">'
    for num, title, body in conditions:
        body_clean = re.sub(r'\s+', ' ', body.split('\n')[0])[:180]
        cond_html += f'''
        <div class="cond-card">
          <div class="cond-num">{num}</div>
          <div><div class="cond-title">{inline(title.strip())}</div>
          <div class="cond-body">{inline(body_clean)}</div></div>
        </div>'''
    cond_html += '</div>'

    # ── triggers HTML ──
    trig_html = '<div class="trigger-list">'
    for i, (trigger, action) in enumerate(triggers, 1):
        trig_html += f'''
        <div class="trigger-item no-break">
          <div class="trigger-icon">!</div>
          <div class="trigger-text"><strong>{inline(trigger)}</strong> — {inline(action)}</div>
        </div>'''
    trig_html += '</div>'

    # ── tests HTML ──
    test_html = '<div class="test-grid">'
    for i, (title, body) in enumerate(tests, 1):
        body_clean = re.sub(r'\s+', ' ', body.strip())[:200]
        test_html += f'''
        <div class="test-card no-break">
          <div class="test-top"><span class="test-num">{i:02d}</span></div>
          <div class="test-title">{inline(title)}</div>
          <div class="test-body">{inline(body_clean)}</div>
        </div>'''
    test_html += '</div>'

    # ── SSA key paragraphs ──
    # First substantive paragraph after VERDICT heading
    verdict_body = ''
    m = re.search(r'VERDICT:.*?\n+(.+?)(?=\n##|\Z)', ssa_md, re.S)
    if m:
        lines = [l.strip() for l in m.group(1).strip().split('\n') if l.strip() and not l.startswith('#')]
        verdict_body = ' '.join(lines[:4])[:500]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{topic_title} — MAD Findings</title>
<style>{BASE_CSS}</style>
</head>
<body>
<div class="wrap">

<!-- ══ COVER ══ -->
<div class="cover">
  <div class="cover-logo">
    <div class="logo-badge">PH</div>
    <span class="logo-text">Phewphonics · MAD Framework</span>
  </div>
  <div class="cover-eyebrow">MAD Run — {today} · AA · DA · SSA</div>
  <h1>{h1}</h1>
  <p class="cover-sub">Full Multi-Agent Debate output — Advocate (AA), Devil's Advocate (DA), and Synthesiser (SSA) verdict. Committed to MAD-SSSOT runs/{slug}/.</p>
  <div class="verdict-chip">{verdict_line}</div>
  <div class="meta-row">
    <span class="meta-pill">MAD Framework</span>
    <span class="meta-pill">AA · DA · SSA</span>
    <span class="meta-pill">{today}</span>
    <span class="meta-pill">{slug}</span>
  </div>
</div>

<!-- ══ SSA VERDICT ══ -->
<div class="section">
  <div class="section-eyebrow">Synthesiser Verdict</div>
  <div class="section-title">SSA Output — Final Verdict</div>
  <div class="section-sub">Synthesised from full AA and DA debate. This is the actionable output.</div>

  <div class="verdict-banner no-break">
    <div class="verdict-label">SSA Final Verdict</div>
    <div class="verdict-title">{verdict_line}</div>
    <p class="verdict-body">{inline(verdict_body)}</p>
  </div>

  <div class="stat-row no-break">
    <div class="stat-tile"><div class="stat-num" style="color:var(--crit)">13</div><div class="stat-lbl" style="color:var(--crit)">Critical Modes</div></div>
    <div class="stat-tile"><div class="stat-num" style="color:var(--sig)">8</div><div class="stat-lbl" style="color:var(--sig)">Significant</div></div>
    <div class="stat-tile"><div class="stat-num" style="color:var(--accent-hi)">6</div><div class="stat-lbl" style="color:var(--accent-hi)">Go Conditions</div></div>
    <div class="stat-tile"><div class="stat-num" style="color:var(--fg-muted)">0</div><div class="stat-lbl" style="color:var(--fg-muted)">IT Tests Catch</div></div>
  </div>
</div>

<!-- ══ CONDITIONS ══ -->
<div class="section page-break">
  <div class="section-eyebrow">Section 2</div>
  <div class="section-title">Go / No-Go Conditions</div>
  <div class="section-sub">All six must be met before go-live. Binary — each is either met or it is not.</div>
  {cond_html}
</div>

<!-- ══ CUTOVER + TRIGGERS ══ -->
<div class="section page-break">
  <div class="section-eyebrow">Section 3</div>
  <div class="section-title">Cutover Sequence &amp; Rollback Triggers</div>
  <div class="section-sub">Strangler Fig — phased by application. Rollback triggers require immediate escalation.</div>

  <div class="seq no-break">
    <div class="seq-step"><div class="seq-label">Week 0</div><div class="seq-app">Prep</div><div class="seq-note">All 6 conditions met. Files checked in.</div><div class="seq-arrow">›</div></div>
    <div class="seq-step"><div class="seq-label">Weeks 1–2</div><div class="seq-app">AutoCAD</div><div class="seq-note">Lowest risk first. xref + sheet set verification.</div><div class="seq-arrow">›</div></div>
    <div class="seq-step"><div class="seq-label">Weeks 3–4</div><div class="seq-app">Inventor</div><div class="seq-note">Latency monitoring. iLogic verification.</div><div class="seq-arrow">›</div></div>
    <div class="seq-step"><div class="seq-label">Weeks 5–6</div><div class="seq-app">Plant 3D</div><div class="seq-note">Last. Operator on-site. Lock file monitoring.</div><div class="seq-arrow">›</div></div>
  </div>

  {trig_html}
</div>

<!-- ══ TEST SCENARIOS ══ -->
<div class="section page-break">
  <div class="section-eyebrow">Section 4</div>
  <div class="section-title">Priority Test Scenarios</div>
  <div class="section-sub">Run these before go-live. In priority order — #1 is the most likely to find a blocker.</div>
  {test_html}
</div>

<!-- ══ AA OUTPUT ══ -->
<div class="section page-break">
  <div class="section-eyebrow">Advocate Agent</div>
  <div class="section-title">AA Output — Strongest Case FOR</div>
  <div class="section-sub">Full advocate position. All arguments for proceeding.</div>
  <div class="prose">{md2html(aa_md)}</div>
</div>

<!-- ══ DA OUTPUT ══ -->
<div class="section page-break">
  <div class="section-eyebrow">Devil's Advocate Agent</div>
  <div class="section-title">DA Output — Strongest Case AGAINST</div>
  <div class="section-sub">Full devil's advocate position. All failure modes and risks.</div>
  <div class="prose">{md2html(da_md)}</div>
</div>

<div class="doc-footer">
  <span>Phewphonics · MAD Framework</span>
  <span>{topic_title}</span>
  <span>{today}</span>
</div>
</div>
</body>
</html>"""


# ── Playwright render ─────────────────────────────────────────────────────────
async def render_pdf(html_path, pdf_path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{html_path}", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        await page.pdf(
            path=str(pdf_path), format="A4", print_background=True,
            margin={"top":"0mm","bottom":"0mm","left":"0mm","right":"0mm"},
        )
        await browser.close()


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-mad-pdf.py <run_folder>")
        sys.exit(1)

    run_dir = Path(sys.argv[1])
    if not run_dir.exists():
        print(f"ERROR: {run_dir} not found"); sys.exit(1)

    # Prefer a hand-crafted print.html if one exists in the run folder
    print_html = run_dir / 'print.html'
    use_custom = print_html.exists()

    # Derive topic title from README
    readme = run_dir / 'README.md'
    topic_title = run_dir.name.replace('-', ' ').title()
    if readme.exists():
        m = re.search(r'^#\s+MAD Run:\s*(.+)', readme.read_text(), re.MULTILINE)
        if m: topic_title = m.group(1).strip()

    slug     = re.sub(r'[^a-z0-9]+', '-', topic_title.lower()).strip('-')
    pdf_name = f"{slug}-MAD-Findings.pdf"
    html_tmp = Path(f"/tmp/mad-print-{slug}.html")
    pdf_out  = run_dir / pdf_name

    print(f"Topic   : {topic_title}")
    print(f"Run dir : {run_dir}")
    print(f"PDF out : {pdf_out}")

    if use_custom:
        print(f"Using hand-crafted layout: {print_html}")
        html_tmp = print_html.resolve()
    else:
        print("Building structured HTML from AA/DA/SSA outputs…")
        html = build_html(run_dir, topic_title)
        html_tmp.write_text(html, encoding='utf-8')
        print(f"HTML: {html_tmp} ({len(html):,} chars)")

    print("Rendering PDF…")
    asyncio.run(render_pdf(html_tmp, pdf_out))

    size = pdf_out.stat().st_size
    print(f"Done: {pdf_out} ({size:,} bytes) ✅")

    if not use_custom and html_tmp.exists():
        html_tmp.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
