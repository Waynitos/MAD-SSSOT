# PLU Migration Status — Cross-Project Index
Last updated: 2026-10-24

This file tracks which claude.ai Projects have the PROJECT-LAUNCH-Plus hook in their instructions.
It doubles as the cross-project discovery index.

---

## Projects

| Project | Domain | PLU Hook | Migrated | Last MAD Run | GitHub Run Folder | Notes |
|---------|--------|----------|----------|--------------|-------------------|-------|
| MAD PROJECT | MAD / Architecture | ✓ pending | 2026-10-24 | PROJECT-LAUNCH-Plus architecture | runs/project-launch-plus-architecture/ | This project |
| INVENTOR - CLEAN SWEEPER SUITE | Inventor / CAD automation | ✗ | — | TRAVERSE iLogic | runs/traverse-ilogic-audit/ | Active — migrate next session |
| STD HANDRAIL PROJECT - CASE STUDIES | Engineering / Handrail | ✗ | — | — | — | Migrate on next use |
| [your other projects] | | ✗ | — | — | — | Add as encountered |

## Standard Instruction Block (paste into Project Settings → Instructions)

```
At session start, fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PROJECT-LAUNCH-Plus.md and apply it. Begin your first response with: ✓ PROJECT-LAUNCH-Plus [version+date] loaded — or — ✗ PROJECT-LAUNCH-Plus fetch failed, proceeding without global config. If a PROJECT-CONFIG.md doc exists in this project, read it after fetching and apply any Overrides section. If no PROJECT-INDEX.md exists yet, fetch https://raw.githubusercontent.com/Waynitos/MAD-SSSOT/main/PLU-wizard.md and run the onboarding wizard.
```

## Migration Steps (per project, ~2 min each)
1. Open the project in claude.ai
2. Go to Project Settings → Instructions
3. Paste the Standard Instruction Block above (prepend to existing instructions)
4. Update this file: mark PLU Hook ✓ and add migrated date
5. Start a new session — wizard runs automatically if project has no PROJECT-INDEX.md

---

## PLU Version History
| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-10-24 | Initial release |
