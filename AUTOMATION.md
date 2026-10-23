# Automation Workflow — MAD-SSSOT

This document defines how authorized agents update the repository without manual file uploads.

## Hybrid Model

| Type of change | Method | Reason |
|----------------|--------|--------|
| New failure modes, horizon notes, knowledge additions (`knowledge/`) | Direct commit | Low risk, additive |
| Changes to core prompts (`prompts/`) or main checklists (`checklists/`) | Pull Request | Protects the protocol DNA |
| README or structural updates | Pull Request | Same reason |

## Token Usage Rules
- A fine-grained Personal Access Token scoped only to this repository is used.
- The token is never stored in the repository or committed.
- Agents must not include the token in any file, comment, or log.

## How an Agent Updates the Repo

### Direct commit (knowledge additions)
1. Clone or pull the latest `main`.
2. Edit or add files only inside `knowledge/`.
3. Commit with a clear message (e.g. `knowledge: add failure mode for offline GPS claims`).
4. Push directly to `main`.

### Pull Request (prompt or checklist changes)
1. Create a new branch (e.g. `update/da-source-quality`).
2. Make the changes.
3. Open a Pull Request against `main` with a short summary of the improvement and why it passed internal MAD review.
4. The repository owner reviews and merges.

## Security
- Token permissions are limited to Contents, Issues, and Pull requests (Read and write) on this repository only.
- Rotate or revoke the token if it is ever exposed.
- Protocol-level changes always go through a Pull Request so the core DNA remains protected.

## Current Status
Hybrid workflow active. Knowledge additions may be direct; prompt and checklist changes require a Pull Request.
