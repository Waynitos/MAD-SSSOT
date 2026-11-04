# MAD Connector Spec
## AA → DA → SSA Data Contract (Harness Paperclip)

> **Purpose:** This document defines the formal data contract between MAD agents.
> It is the "paperclip" — the binding spec that connects agent outputs to agent inputs
> so every RMAD run is consistent, auditable, and automation-ready.
>
> **Status:** v1.0 — 2026-11-04. Owned by SA. Update when agent prompts or SSA format changes.

---

## 1. Overview

The MAD execution chain is:

```
[Topic Input]
      │
      ▼
  ┌───────┐    Full topic + context
  │  AA   │ ──────────────────────────────────────────────────► AA-output.md
  └───────┘
      │
      │  AA-output.md passed in full to DA
      ▼
  ┌───────┐    Full topic + AA-output.md
  │  DA   │ ──────────────────────────────────────────────────► DA-output.md
  └───────┘
      │
      │  AA-output.md + DA-output.md passed in full to SSA
      ▼
  ┌───────┐    Full topic + AA-output.md + DA-output.md
  │  SSA  │ ──────────────────────────────────────────────────► SSA-output.md
  └───────┘
      │
      ▼
  GitHub commit → runs/[topic]/
  (AA-output.md, DA-output.md, SSA-output.md, README.md)
```

---

## 2. Input Contract — What Each Agent Receives

### AA (Advocate Agent)
| Field | Required | Content |
|---|---|---|
| `topic` | ✅ | The question, decision, or domain under analysis |
| `context` | Optional | Any background, constraints, or prior SSA outputs the user provides |
| `mode` | Optional | Auto / Expert / Heavy (default: Auto) |

**AA receives:** Topic + context only. It must NOT receive DA or prior SSA outputs (would bias the affirmative case).

---

### DA (Devil's Advocate Agent)
| Field | Required | Content |
|---|---|---|
| `topic` | ✅ | Same topic as given to AA (verbatim) |
| `AA-output.md` | ✅ | Full, unedited AA output — no summaries, no excerpts |
| `context` | Optional | Same context as given to AA |
| `mode` | Optional | Same mode as AA run |

**DA receives:** Topic + full AA output. It critiques both the topic AND AA's case.
**Critical rule:** DA must ALWAYS receive the complete AA-output.md, not a summary. Summaries hide the gaps DA must find.

---

### SSA (Synthesiser Agent)
| Field | Required | Content |
|---|---|---|
| `topic` | ✅ | Same topic (verbatim) |
| `AA-output.md` | ✅ | Full, unedited AA output |
| `DA-output.md` | ✅ | Full, unedited DA output |
| `context` | Optional | Same context as prior agents |
| `checklists` | Optional | Relevant checklist files from `/checklists/` (e.g. MAD_Device_SWAT_Arsenal.md) |
| `mode` | Optional | Same mode — escalate to Heavy if residual uncertainty stays high |

**SSA receives:** Topic + full AA + full DA. It synthesises, never adjudicates.

---

## 3. Output Contract — What Each Agent Produces

### AA-output.md
```markdown
# AA Output — [Topic]
**Run date:** YYYY-MM-DD
**Mode:** [Auto / Expert / Heavy]

## Strongest Case FOR
[Core affirmative argument]

## Supporting Evidence
[Facts, data, reasoning that back the case]

## Options / Variants
[If multiple approaches exist, lay them out]

## Confidence
[High / Medium / Low — brief rationale]
```

---

### DA-output.md
```markdown
# DA Output — [Topic]
**Run date:** YYYY-MM-DD
**Mode:** [Auto / Expert / Heavy]

## Critique of AA Case
[Direct attack on AA's reasoning, evidence, and gaps]

## Gaps / Unasked Questions
[What AA didn't address that matters]

## Failure Modes
[What could go wrong with the affirmative position]

## Risks and Downsides
[Costs, consequences, edge cases]

## Residual Questions
[What DA cannot resolve — surfaces for SSA]
```

---

### SSA-output.md
```markdown
# SSA Output — [Topic]
**Run date:** YYYY-MM-DD
**Mode:** [Auto / Expert / Heavy]

## Executive Summary
[2–3 sentence verdict: what the debate settled]

## High-Confidence Findings
[Claims both AA and DA agree on, or DA failed to dent]

## Contested Territory
[Where AA and DA genuinely disagree — both sides preserved]

## Residual Uncertainty
[What remains unresolved and why — made explicit, not hidden]

## Recommended Next Step
[Single best action, or dual-comparison if two paths are close]

## Horizon Analysis
[What would change this verdict in 6–12 months]
```

---

### README.md (run-level)
```markdown
# MAD Run — [Topic]
**Date:** YYYY-MM-DD | **Mode:** [Auto/Expert/Heavy]

## Topic
[Full topic statement]

## Verdict (SSA one-liner)
[Copied from SSA Executive Summary, first sentence only]

## Files
- AA-output.md — Affirmative case
- DA-output.md — Devil's Advocate critique
- SSA-output.md — Synthesis and verdict

## Notes
[Any flags, escalation notes, or follow-up items]
```

---

## 4. Run Folder Naming Convention

```
runs/[topic-slug]/
```

Where `topic-slug` is:
- Lowercase, hyphenated
- Max 40 characters
- Descriptive of the topic, not the date
- Date is captured inside each file, not the folder name

**Examples:**
```
runs/mac-vs-pc-dev-setup/
runs/github-actions-vs-local-runner/
runs/mad-connector-spec-design/
```

---

## 5. Mode Scaling Rules

| Mode | When to use | Agent token budget |
|---|---|---|
| **Auto** | Standard decisions, most RMAD runs | Default |
| **Expert** | High-stakes or technically complex topics | Elevated |
| **Heavy** | Residual uncertainty stays high after Auto/Expert | Maximum — use sparingly |
| **Ensemble** | Critical decisions needing multi-run coverage | Run 2–3 independent cycles, compare SSA outputs |

---

## 6. Escalation Triggers

A run should escalate to a heavier mode or a full Ensemble when:
- DA finds **3 or more critical gaps** in AA's case
- SSA's residual uncertainty is rated High
- The decision is **irreversible** (major capital, system cutover, go/no-go)
- The topic domain changed significantly since the last run on this subject

---

## 7. What This Spec Enables (Automation Readiness)

This contract is designed to be automation-ready for Phase 2 (GitHub Actions / API harness):

| Automation step | Maps to this spec |
|---|---|
| Trigger word RMAD | Initiates run, sets topic + mode |
| Spawn AA | Receives: topic + context |
| Spawn DA | Receives: topic + AA-output.md (full) |
| Spawn SSA | Receives: topic + AA-output.md + DA-output.md (both full) |
| Commit outputs | Writes to `runs/[topic-slug]/` following output contract |
| Update index | Appends to PROJECT-INDEX.md / SSSOT index |

A Python harness or GitHub Action implementing this spec requires no prompt engineering beyond what is already in `prompts/` and `MAD_Agent_Prompts.md`.

---

## 8. Version History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-04 | Initial connector spec — Option A formalisation |

---

*This document is maintained by SA as part of the living knowledge base.*
*Trigger a MAD run on this spec itself if the contracts become stale.*
