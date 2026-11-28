# Evidence-First Instructions — No Guesswork Delegated to the User

**Status:** CEO-directed operational protocol, 28 November 2026 (Australia/Brisbane)  
**Scope:** BEEXCITED development, assistants, research, user-facing instructions, troubleshooting and platform acceptance.  
**Origin:** Penelope/Open WebUI UI-setting navigation error during Flight 05.  
**Principle:** The assistant must perform the verification work before giving the user steps. Do not make the user discover the true answer through trial and error.

## Failure that triggered this directive

During Penelope Flight 05, the assistant repeatedly directed the CEO to menus without first verifying the **installed Open WebUI v0.13.4**, screenshot evidence, exact UI context or feature availability. It conflated a **Workspace > Models editor**, **Personal > Interface settings** and **Admin Panel > Settings > Interface**, suggested settings that might appear only in other versions, and shifted the burden of finding the correct navigation onto the user. This defeats the reliability objective of BEEXCITED itself.

This failure mode is not solved by apologising or collecting notes alone. Apply this protocol **immediately within development work**, not merely as a future platform feature.

## Mandatory verification gate, before giving actionable steps

1. **Identify actual environment:** application, installed version/build, platform/device, permissions, current screen/page and goal. Use already-provided screenshots, records and earlier test results. Do not ask the user for facts already supplied.
2. **PRESEARCH before directing:** inspect the actual UI/evidence and the relevant version-specific official docs/source or existing functioning pattern. Prefer the product's proven built-in mechanism (Just Use Pencil) over speculative reconstruction.
3. **Cross-check before instructing:** distinguish similar but different configuration surfaces (user vs admin vs workspace vs model, etc.). Verify the named control, its path, whether available in the user's version, and whether a setting is read-only, safe or production-affecting. A general current-doc location is **not** proof a specific installation exposes it.
4. **State evidence status accurately:** use **VERIFIED IN USER UI**, **VERIFIED IN VERSION-MATCHED SOURCE/DOCS**, **DOCUMENTED FOR ANOTHER VERSION**, **INFERRED / NOT VERIFIED**, or **UNAVAILABLE**. Never describe a guess as confirmed.
5. **Provide one precise action at a time:** exact start screen, click path, field label, expected visual result and rollback if applicable. No menu mazes, no repeated requests to inspect an already-shown screen.
6. **If not verifiable, stop guessing:** explicitly say what is unknown and what minimal non-destructive check would establish it. Do the research yourself when tools allow; involve the CEO only for user-only access or validation.
7. **Test instruction quality:** measure first-try navigation success, number of incorrect paths, number of user corrective screenshots, unnecessary clicks, and time lost to assistant-directed trial-and-error. Treat failures as development defects; document cause and preventive correction.
8. **Apply evidence-first to the work itself:** agents designing BEEXCITED must obey the same standards they are intended to enforce in the eventual platform. Research, accuracy, UX and reliability are not deferred until launch.

## Decision hierarchy

**Current UI / verified deployed configuration > verified version-matched documentation/source > reproducible working precedent > general documentation > inference.** If conflicting evidence is found, reconcile it before instructing. Do not claim access to a live UI or installed configuration unless actually observed.

## Response contract for navigation / configuration

- **What I verified:** concise, sourced statement of the current screen/setting and any uncertainty.
- **Do this:** single specific action grounded in the verified state.
- **Expected result:** exact indicator or control visible after that action.
- **Do not change:** safety/production constraints where applicable.
- Avoid flooding the user with speculative alternatives.

## Acceptance criteria

- No unverified navigation paths presented as facts.
- No asking the user to hunt for a control that the assistant could first verify using available evidence.
- Installed-version compatibility explicitly handled.
- User screens are interpreted accurately and not conflated with similar pages.
- A failure results in immediate changed behaviour plus a linked issue/test case.
- Corrected instructions pass an owner screenshot/reality check on first attempt.

## Integration / limits

Cross-project rule intended for all BEEXCITED agents and workflows using MAD-SSSOT/PLU. This document records the directive and must be **explicitly loaded or integrated into the relevant runtime prompts or project instructions**; saving to GitHub alone does not automatically modify existing agent behaviour or external ChatGPT sessions. No code, server or production settings changed by this governance record.

Related: [PROJECT-LAUNCH-Plus.md](../PROJECT-LAUNCH-Plus.md), [PLU-presearch-protocol.md](../PLU-presearch-protocol.md), and [Penelope Flight 05 issue #24](https://github.com/Waynitos/BEEXCITED-AI/issues/24).
