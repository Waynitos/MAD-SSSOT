# Topic Type: Script Audit

**Use for:** Reviewing Python, iLogic, LISP, PowerShell, AutoIt, or other scripts for correctness, robustness, performance, and IT compliance — OR deep-diving a problem the current script hasn't cracked yet.

## Two Modes — choose one before starting

### Mode A: Full Code Audit
Paste the script. The MAD cycle audits what it does, finds bugs, assesses performance and security, and generates test scaffolding.

### Mode B: Unsolved Problem Deep Dive
Describe the problem the script needs to solve and what it currently does wrong or can't do. Paste the current (failing/incomplete) script if one exists. The MAD cycle attacks both the approach *and* the code, then proposes alternative strategies.

**If no script exists yet:** describe the problem and the environment (language, host app, inputs/outputs). The SSA will propose an implementation approach plus starter scaffolding.

---

## AA Framing

### Mode A (Code Audit)
Analyse the script and build the strongest case for what it does well. Cover:
- Does it achieve its stated goal?
- Is the logic sound and readable?
- Does it handle the expected inputs correctly?
- Does it run at acceptable speed for its use case?
- Note any particularly clean, efficient, or clever patterns.

### Mode B (Unsolved Problem)
Build the strongest case for the current approach. What is it trying to do? What does it get right, even partially? What is the hardest part of the problem and why is it genuinely difficult? Explore alternative approaches that might solve it — including whether a different language or tool would be a better fit.

---

## DA Pressure Angles

### Always apply

**Correctness & robustness**
- Edge cases: what inputs or states were NOT considered?
- Error handling: what happens on failure — silent fail, crash, corrupt output?
- Boundary conditions: empty input, null values, max/min values, unexpected types
- Logic errors: off-by-one, wrong operator, incorrect condition
- Does it leave the system in a clean state on exit or error?
- Is there a test or validation step, or does it run blind?

**Performance & scalability**
- How fast does it run? Is that acceptable for its use case and data volume?
- Does it scale? Any O(n²) traps, unnecessary loops, or repeated expensive calls?
- Does it load things it doesn't need (entire files, full object hierarchies)?
- Is there a built-in function or library call that would replace a slow hand-written loop?
- **Is there a faster language or runtime for this task?** (e.g. Python for data processing where LISP is used, PowerShell for Windows admin tasks currently done in AutoIt, compiled vs interpreted for high-volume runs)
- Does it hold resources (file handles, COM objects, database connections) open longer than needed?

**Maintainability & portability**
- Hardcoded values that should be parameters or config
- File/path assumptions that break on different machines or environments
- Version-specific API calls that will break on upgrade (especially Inventor/AutoCAD API versions)
- For iLogic/LISP specifically: CAD object assumptions, document state dependencies, undo/transaction handling
- Is the code readable by someone who didn't write it?

**Security & IT compliance**
- Does it expose, log, or transmit credentials or personal data?
- Does it write to unsafe paths (system directories, shared drives without permission check)?
- Does it accept unsanitised external input (file names, user text, environment variables)?
- Does it download or execute code from the network at runtime?
- Does it require elevated privileges, and is that necessary?
- **Is this language/runtime permitted under corporate IT policy?** (Python, PowerShell execution policy, AutoIt — flag any that commonly trigger AV or policy blocks)
- Does it phone home, write to registry in unexpected places, or create scheduled tasks?
- Could it be used as a vector by a malicious actor with access to the machine?

### Mode B additional angles
- Is the chosen approach fundamentally right for this problem, or is there a better paradigm?
- What assumption in the current code is most likely causing the failure?
- Has this problem already been solved by a library or built-in the author hasn't used?
- What would need to change in the environment (API, permissions, data format) for the current approach to work?
- Would a different language solve this more cleanly — and is that language available in this environment?

---

## SSA Requirements

### Mode A output
- List confirmed bugs or logic errors (high confidence)
- List suspected issues that need testing to confirm (lower confidence)
- Provide corrected code or specific fix recommendations for each issue
- **Performance verdict:** Is this the fastest reasonable approach for its task? If not, what would be faster and by how much?
- **Language verdict:** Is this the right language for this task? If a switch would be materially better, say so and why.
- **Security/IT verdict:** Does it have any IT policy risks? Flag any that would likely be blocked by corporate AV, execution policy, or network controls.
- Rate overall robustness: **Production-ready / Needs hardening / Prototype only**
- Suggest the 1–2 highest-priority fixes if the user can only do a few
- Generate unit test scaffolding (see Unit Testing section below)

### Mode B output
- Diagnose the root cause of the current failure or limitation
- Propose 2–3 alternative approaches ranked by likelihood of success
- For the top approach: provide revised or starter code
- Flag which parts require the runtime environment to validate

---

## Unit Testing

A MAD audit generates test scaffolding without needing the live environment. For each test, it flags:
- ✅ **Logic-only** — can be validated by reading the code; no environment needed
- ⚠️ **Needs runtime** — depends on file system, CAD API (Inventor/AutoCAD objects), external connections, or OS state

### What gets generated without the environment
- Input/output test cases for pure functions
- Edge case assertions (null, empty, boundary values)
- Control flow path coverage outline
- For iLogic: mock-structure stubs showing which Inventor API calls need a live document

### What requires the environment to confirm
- Anything touching `ThisDoc`, `ThisApplication`, or Inventor document properties
- File read/write operations
- Registry or COM calls
- Network or database connections

**Instruction to SSA:** Always generate tests for logic-only paths. For runtime-dependent calls, generate the stub and mark it ⚠️ Needs runtime.

---

## Checklist
→ checklists/script-audit.md (to be created)

## Environment note
Always state the language and host application (e.g. "Python 3.11 / standalone", "iLogic / Autodesk Inventor 2024", "LISP / AutoCAD 2025", "PowerShell 5.1 / Windows Server"). This determines which API assumptions, performance characteristics, and IT policy risks the DA should pressure-test.
