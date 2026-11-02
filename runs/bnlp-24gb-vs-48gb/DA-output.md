# DA Output — BNLP: 24GB vs 48GB Unified Memory
**Run date:** 2026-10-24 | **Project:** BNLP | **Trigger:** RMAD

---

## Devil's Advocate Brief: The Case Against 24GB

**Opening Challenge:** The 24GB argument sounds reasonable until you examine the actual workflow. Waynito isn't buying a general-purpose laptop — he's buying a machine specifically to run AI work with Claude. That single fact changes the calculus entirely. Optimising for budget on the RAM of an AI workstation is like buying a work truck and skimping on the tray.

### 1. The Parallels Scenario Is Your Worst Case, And You're Planning It
This isn't a hypothetical. Waynito has explicitly flagged running Inventor via Parallels. On 24GB, allocating a responsible 10GB to the Windows VM leaves 14GB for macOS — after which the OS takes its cut, leaving roughly 10–12GB for actual work. Claude running via browser, 10+ tabs, and anything else in macOS will hit that ceiling fast. Swap kicks in. NVMe takes the wear. Latency spikes. You bought a performance machine and immediately hobbled it.

### 2. The Upgrade Is Permanent — The Risk Is Asymmetric
You cannot add RAM later. You can, however, not use RAM you have. The downside of 48GB you don't need: zero. The downside of 24GB you do need: degraded performance for the entire ownership period, with no exit. On a non-upgradeable system, you are not choosing RAM for today — you are choosing it for 2031.

### 3. Local AI Is the Direction of Travel
If Waynito is serious about AI work, local inference is not a distant curiosity — it's already practical and accelerating. At 24GB, usable model weight budget is ~17GB: capable, but capped at 14B models. At 48GB, that jumps to ~35GB, unlocking 32B models — a genuine capability difference, not a marginal one. Buying the AI laptop that can't run serious local AI models is a specific kind of irony.

### 4. The Maths Don't Justify the Risk
$600 over five years is $120/year — less than a single software subscription. At that amortisation, the argument for 24GB is not "I'm saving money," it's "I'm accepting meaningful constraints for $2.30 a week."

### 5. Memory Pressure Compounds Over Time
Apps get heavier. AI tooling gets hungrier. What is marginal pressure in 2026 becomes routine pressure in 2028. Apple's fast swap buys time — it doesn't eliminate the problem. You're betting the performance holds for five years on a budget decision made today.

---

**Closing:** The 24GB position depends on everything staying exactly as it is — workloads, software appetite, and Waynito's ambitions — for five years on a sealed, non-upgradeable device. That is not a safe assumption. The $600 difference is not between comfortable and luxurious. It's between adequate-today and capable-for-the-duration. On a machine bought specifically for AI work, this is not the place to cut.
