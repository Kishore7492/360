# OWNER BRIEF

## Section 6
### Confidence Architecture Audit (Confirmed 2026-04-09)
- PR09 SignalScoringEngine is the final authority.
- Layers 2 and 3a are overwritten/dead for final confidence.
- Universal/global scoring is structurally wrong for several path families.
- Target design is a hybrid model: shared base plus path-family-specific thesis scoring.

**Critical Confirmed Mismatches:**
- Soft-gate penalties overwritten.
- LIQUIDATION_REVERSAL missing from SMC exemptions.
- FUNDING_EXTREME_SIGNAL missing from SMC exemptions.
- EMA scoring penalizing reversal paths.
- Order-flow thesis absent from final score.

## Section 7
### PR Log
- **PR-ARCH-5** — merged/ready state should reflect that it introduces a DIVERGENCE_CONTINUATION-specific QUIET floor of 64.0 while keeping the global 65.0 floor.
- **PR-ARCH-6** — planned next implementation: correct _SMC_GATE_EXEMPT_SETUPS by adding LIQUIDATION_REVERSAL and FUNDING_EXTREME_SIGNAL, and likely DIVERGENCE_CONTINUATION after quick confirm. Expected outcome is to stop structural false suppression by the SMC hard gate.

### Confidence Architecture Roadmap
- **Phase C1:** Scoring integrity fix (restore soft penalties after PR09 final score instead of letting them be overwritten).
- **Phase C2:** Family-based scoring model (trend / reversal / order-flow-positioning / quiet-specialist).
- **Phase C3:** Cleanup of dead legacy confidence machinery after migration.

## Section 8
### Thresholds Quick Reference
- _QUIET_DIVERGENCE_MIN_CONFIDENCE = 64.0
- Update any SMC/QUIET entries to reflect post-ARCH-5 status.

## Section 10
### Current State Snapshot
- ARCH-2/3/4 merged.
- ARCH-5 created and/or awaiting review as appropriate.
- Divergence path now confirmed alive in logs but blocked near threshold before ARCH-5.
- Confidence-architecture audit complete with hybrid target design chosen.

## Section 11
### Notes Log
- **2026-04-09:** Confidence architecture audit findings and decision to move toward a hybrid confidence model rather than fully global or fully per-path.

## Section 12
### Session History
- **2026-04-09:**
  - Monitor review after ARCH-3/4.
  - Discovery that 360_SCALP_DIVERGENCE is alive but blocked by QUIET_SCALP_BLOCK at 64.3 < 65.0.
  - Creation/review of PR-ARCH-5.
  - Completion of the deep confidence audit.
  - Decision that hybrid scoring is the target.
  - Next planned PR-ARCH-6 for SMC exemption corrections.
