# OWNER_BRIEF.md Integrity Record

This file is the canonical reference for OWNER_BRIEF.md integrity checking.
Every Copilot session must check this file if OWNER_BRIEF.md appears short or corrupted.

## Current Canonical Version

| Field | Value |
|---|---|
| Commit SHA | efad0286557e342194453606b2bd94a073b1ff43 |
| Blob SHA | 60860afdef86a39c6014260429d4278806741ffd |
| Line count | 1656 |
| Date verified | 2026-04-10 |
| Verified by | Copilot + owner (mkmk749278) |

**Note:** The commit SHA and blob SHA above are from the pre-redesign snapshot (2026-04-09, 801-line version). They serve as the fallback restoration reference. After the redesign PR (2026-04-10) merges to main, update these to the post-merge commit SHA and blob SHA. The line count (1656) reflects the current redesigned version.

## Restoration Instructions

If OWNER_BRIEF.md is found to be under 1000 lines at session start:

1. **Stop immediately** — do not proceed with the session
2. **Alert the owner** — "OWNER_BRIEF.md appears corrupted (N lines). Restoring from canonical version."
3. **Fetch the canonical version** — use this priority order:
   - **Primary:** fetch `OWNER_BRIEF.md` from `main` HEAD at `mkmk749278/360-v2` — this is always the most current authoritative version
   - **Fallback:** if main is inaccessible, use the commit SHA from the table above as a reference point, then rebuild from there
4. **Compare** — identify what is missing vs the expected content
5. **Restore** — write the restored + updated version back to main via PR
6. **Update this file** — update the commit SHA, blob SHA, and line count after restoration

## Update Instructions

After every session that updates OWNER_BRIEF.md:
1. Note the new commit SHA of main after the merge
2. Note the new blob SHA of OWNER_BRIEF.md at that commit
3. Note the new line count of OWNER_BRIEF.md
4. Update this file with the new values via the same PR or a follow-up commit

## Why This Exists

Copilot sessions receive OWNER_BRIEF.md as a chat context attachment tied to a specific commit.
If that commit is older or shorter than main, and Copilot writes back using that as its base,
lines added in later sessions are silently lost.

This file provides a hard checkpoint: if the brief is ever shorter than the canonical line count,
something went wrong and must be fixed before any work proceeds.

## Rule

> OWNER_BRIEF.md must NEVER get shorter between sessions.
> Every session appends. Nothing is ever removed except by explicit owner instruction.
> If it shrinks, treat it as data corruption and restore immediately.