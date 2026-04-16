# ACTIVE CONTEXT

## Current Phase
The repository is in the post-PR-1-through-PR-5 execution phase with healthy infrastructure, healthy telemetry, and stronger runtime observability, but it remains not validation-ready because zero paid-signal expression persists and the dominant current blocker is reclaim/retest geometry rejection rather than MTF policy.

## Current Active Priority
1) Restore continuity truth to match the current repo/runtime roadmap  
2) Execute the next bounded reclaim/retest geometry policy repair on the active 360_SCALP path  
3) Reassess scoring-ceiling pressure only after geometry unlock is tested live

## Current Known Live Issues
- Zero emitted paid signals remain the primary business problem despite healthy engine/runtime state.
- Reclaim/retest geometry rejection is the dominant code-side blocker, especially FAILED_AUCTION_RECLAIM and SR_FLIP_RETEST.
- MTF refinement is no longer the next roadmap item because family-aware MTF refinement already landed in PR-1.
- Duplicate lifecycle / terminal event integrity still matters, but it is secondary until expression resumes.
- Specialist rollout governance exists and divergence is in limited-live pilot mode, but this has not translated into emitted flow.
- Coding-agent execution is blocked by GitHub Actions/Copilot billing or spending issue.

## Next PR Queue
- Priority 1: PR-6 reclaim/retest geometry policy repair for FAILED_AUCTION_RECLAIM and SR_FLIP_RETEST, narrowly scoped to risk_distance_too_tight and SL-cap/R:R interaction without broad loosening  
- Priority 2: PR-7 active-path scoring ceiling reassessment only if geometry repair still leaves all survivors in WATCHLIST  
- Priority 3: PR-8 duplicate lifecycle / terminal event integrity hardening  
- Priority 4: PR-9 continuity and operating truth sync  
- Priority 5: PR-10 specialist pilot reassessment after core paid-path expression returns

## Roadmap Truth (Current)
- PR-1: Family-aware 360_SCALP MTF gate refinement with per-family suppression telemetry — merged.
- PR-2: Post-predictive SL/TP geometry revalidation with geometry delta telemetry — merged.
- PR-3: Channel runtime-role truth made explicit and volatile pre-skip scoping refined — merged.
- PR-4: End-to-end setup-path observability across the scanner funnel and lifecycle outcomes — merged.
- PR-5: Fail-closed specialist rollout states with limited-live divergence pilot — merged.
- Next roadmap move is not more MTF loosening; it is bounded geometry repair on reclaim/retest families.

## Open Risks
- Continuity drift can still mis-sequence future sessions if ACTIVE_CONTEXT is not kept aligned with merged roadmap truth.
- Geometry repair could accidentally become broad loosening if family boundaries are not held tightly.
- If geometry is repaired and survivors still cap at 50–64, the next true bottleneck will be scoring architecture rather than gating.
- Healthy infra and rich telemetry can create false comfort while business validation remains blocked.

ACTIVE_CONTEXT synced to current roadmap truth as of 2026-04-16.