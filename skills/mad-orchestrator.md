# SKILL: MAD Orchestrator

**Trigger phrases:** "Run MAD on", "MAD run", "run this through MAD", "kick off a MAD on"

When the user says any of the above followed by a subject and optional topic type, execute the full AA→DA→SSA cycle automatically with zero manual steps.

---

## Step 1 — Identify subject and topic type

Parse the user's message for:
- **Subject:** what they want analysed (required)
- **Topic type:** one of: `compare-items`, `price-ferret`, `flight-assassin`, `research`, `script-audit`, `enterprise-adoption`, `general-mad`

If topic type is not stated, infer it from the subject. If genuinely ambiguous, ask one question only: "Which topic type — [two most likely options]?"

Confirm to the user in one line: *"Running MAD on [subject] · [topic type] — AA agent starting now."*

---

## Step 2 — Fetch topic config

Read the topic config from the repo:
- `/home/claude/mad-sssot/topics/[topic-file].md`

Topic file mapping:
- `compare-items` → `topics/compare-items.md`
- `price-ferret` → `topics/price-ferret.md`
- `flight-assassin` → `topics/flight-assassin.md`
- `research` → `topics/research.md`
- `script-audit` → `topics/script-audit.md`
- `enterprise-adoption` → `topics/enterprise-software-adoption.md`
- `general-mad` → `topics/general-mad.md`

Extract: AA framing, DA pressure angles, SSA requirements.

---

## Step 3 — Spawn AA agent (background)

Launch a fork with `run_in_background: true`.

AA prompt structure:
```
You are the Advocate Agent (AA) in a MAD cycle. Build the strongest, most complete case possible. Do not balance preemptively.

Topic framing:
[AA framing from topic config]

Subject: [user's subject]
```

For `enterprise-adoption` add:
```
IMPORTANT: State ALL known integration constraints and documented failure modes for this environment BEFORE beginning. Do not let them emerge mid-analysis.
```

For `script-audit` include the mode (A or B) and ask user to paste script if not already provided.

---

## Step 4 — Spawn DA agent (background, after AA completes)

When AA fork completes, immediately launch DA fork with `run_in_background: true`.

DA prompt structure:
```
You are the Devil's Advocate Agent (DA) in a MAD cycle. Find every gap, weakness, omission, risk, and failure mode. Be rigorous — do not lightly qualify.

Pressure angles:
[DA pressure angles from topic config]

SOURCE QUALITY AUDIT (mandatory):
- Flag claims older than 6 months on fast-moving topics
- Flag secondary-only sources
- Flag single-outlet claims needing corroboration

AA output: [full AA output]
Original subject: [user's subject]
```

---

## Step 5 — Spawn SSA agent (background, after DA completes)

When DA fork completes, immediately launch SSA fork with `run_in_background: true`.

SSA prompt structure:
```
You are the Synthesizer Agent (SSA) in a MAD cycle. Integrate the AA and DA outputs into a final tested synthesis.

Requirements:
[SSA requirements from topic config]

Separate high-confidence from contested findings. List residual uncertainties. Close with next-best alternatives and a horizon analysis.

AA output: [full AA output]
DA output: [full DA output]
Original subject: [user's subject]
```

---

## Step 6 — Deliver results

When SSA completes:

1. **Reply with 3–5 bullet summary** — the verdict, key findings, and one recommended next action. Keep it short enough to read on a phone.

2. **Publish SSA output as artifact** — full structured report with AA/DA/SSA sections, risk register, next steps.

3. **Save to repo** — write SSA output to `runs/[slug]/SSA-output.md`. Create the folder if it doesn't exist. Also save AA and DA outputs as `AA-output.md` and `DA-output.md`.

4. **Commit** with message: `feat: MAD run — [subject] ([topic type])`

5. **Show checklist pill** if the topic has a checklist — name the file so the user knows it exists.

---

## Parallel runs

If the user says "Run MAD on these: [list]" — launch all AA forks simultaneously in a single response. Each pipeline (AA→DA→SSA) runs independently. Deliver each result as it completes, not waiting for all to finish.

---

## Isolation note (documented tradeoff)

Forked MAD agents are not fully isolated from the parent session's context — the parent has processed prior outputs before constructing each fork's prompt. This is weaker than manual three-separate-sessions MAD. It is accepted for Phase 1 as the tradeoff that makes MAD actually usable. For highest-stakes decisions, manual MAD remains the gold standard.

---

## Error handling

- If a fork produces very short or clearly low-quality output: flag it to the user and offer to re-run that agent.
- If GitHub write fails: deliver the artifact and summary anyway, note the commit failed, offer to retry.
- If topic config not found: fall back to `general-mad` framing and note the fallback.
