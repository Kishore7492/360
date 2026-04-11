# 360 Crypto Eye — Active Context (Continuity Companion)

> **Purpose:** This file is read at every Copilot session start alongside `OWNER_BRIEF.md`.
> It records current phase, active priority, known live issues, the next PR queue, and open risks.
> It is updated at every session end. It complements the canonical brief — it does not replace it.
> Keep it compact. Every field must be accurate or marked unknown.

---

## Current Phase

**Phase:** 6.1 — Live Architecture Validation (active)

Architecture correction sequence (ARCH-2 through ARCH-10) is complete.
Active roadmap is the business-first signal-engine path sequence (OWNER_BRIEF.md Part VI §6.2).
Steps 1–8 complete. Zero-signal observability PR is the pre-step-9 blocker.
Step 9 (path-by-path portfolio tuning) remains gated on live evidence.

### Roadmap completion state

| Step | Description | Status |
|---|---|---|
| 1 | Refine `VOLUME_SURGE_BREAKOUT` | ✅ merged |
| 2 | Refine `BREAKDOWN_SHORT` | ✅ merged |
| 3 | Refine `SR_FLIP_RETEST` | ✅ merged |
| 4 | Review `WHALE_MOMENTUM` role | ✅ merged |
| 5 | Add `CONTINUATION_LIQUIDITY_SWEEP` | ✅ merged |
| 6 | Add `POST_DISPLACEMENT_CONTINUATION` | ✅ merged |
| 7 | Add `FAILED_AUCTION_RECLAIM` | ✅ merged (PR #105) |
| 8 | Formalize path portfolio roles | ✅ merged (PR #106) |
| Pre-9 | Diagnose zero live signal — observability fix | ✅ current PR |
| 9 | Path-by-path portfolio tuning | ⏳ next (needs live signal data) |

---

## Current Active Priority

1. **Gather live diagnostic evidence** — MTF gate and below-threshold scoring rejections are now visible in suppression summary (key: `score_below50:<chan>`). Next step: review suppression counts to understand what funnel stage is blocking candidates.
2. **Step 9: Path-by-path portfolio tuning** — next roadmap item. Requires live diagnostic evidence (candidate rate, emit rate, gate-block distribution) before any threshold adjustments.

---

## Zero-Signal Diagnosis — Confirmed Fixes in Current PR

### Fix 1 — `_select_indicator_weights` missing `"mean_reversion"` key
- **Evidence:** 6 pre-existing test failures in `test_phase4_adaptive_logic.py` (`KeyError: 'mean_reversion'`).
- **Fix:** Added `"mean_reversion"` key to all regime branches. Values: VOLATILE=0.8, RANGING/QUIET=1.2, TRENDING=0.7, default=1.0.
- **Note:** `RANGE_FADE` evaluator is permanently removed per OWNER_BRIEF.md. The `"mean_reversion"` weight key is retained as a valid regime-weighting dimension (no evaluator currently uses it as a primary weight, but it fixes the pre-existing KeyError and documents the relative weight for any future brief-approved mean-reversion path).

### Fix 2 — MTF hard gate not tracked in suppression_counters (High observability gap)
- **Evidence:** `_prepare_signal` returned `None, None` at MTF gate with only a debug log. Suppression summary never showed MTF as a rejection cause.
- **Fix:** Added `self._suppression_counters[f"mtf_gate:{chan_name}"] += 1` and `suppression_tracker.record()` at MTF gate rejection.

### Fix 3 — Below-threshold rejection not logged
- **Evidence:** Below-threshold score branch returned `None` with no log or counter.
- **Fix:** Added `log.debug()` with full component breakdown and `self._suppression_counters[f"score_below50:{chan_name}"] += 1`.
  (Key was originally named `pr09_below50`; renamed to `score_below50` in PR-09 cleanup for operator clarity.)

---

## Current Known Live Issues

| Issue | Severity | Status |
|---|---|---|
| Zero live signal output — root cause not yet confirmed from live data | Critical | Observability improved in current PR — live suppression summary needed |
| `ScanLat=~20398ms` — elevated scan latency | High | Cause not confirmed — not a code defect in signal path |
| Heartbeat file missing after grace period | Medium | Needs trace — may be related to long scan latency |
| Score < 50 rejections previously silent | Medium | Fixed — now logged and counted in suppression summary as `score_below50:<chan>` |
| MTF gate rejections previously silent | High | Fixed — now counted in suppression summary |

---

## Next PR Queue

| Priority | PR | Description | Gate |
|---|---|---|---|
| 1 | PR-9 | Path-by-path portfolio tuning (evidence-led, per `ACTIVE_PATH_PORTFOLIO_ROLES`) | Live signal data required first |

Full current roadmap: `OWNER_BRIEF.md` Part VI section 6.2.

---

## Portfolio Role State (step 8 output)

Introduced in `src/signal_quality.py`:
- `PortfolioRole` enum: `core`, `support`, `specialist`
- `ACTIVE_PATH_PORTFOLIO_ROLES` dict: explicit role for all 14 active evaluators
- `APPROVED_PORTFOLIO_ROLES` frozenset: taxonomy guard for future additions

Role assignments:
- **core (7):** `LIQUIDITY_SWEEP_REVERSAL`, `TREND_PULLBACK_EMA`, `VOLUME_SURGE_BREAKOUT`, `BREAKDOWN_SHORT`, `SR_FLIP_RETEST`, `CONTINUATION_LIQUIDITY_SWEEP`, `POST_DISPLACEMENT_CONTINUATION`
- **support (4):** `LIQUIDATION_REVERSAL`, `DIVERGENCE_CONTINUATION`, `OPENING_RANGE_BREAKOUT`, `FAILED_AUCTION_RECLAIM`
- **specialist (3):** `WHALE_MOMENTUM`, `FUNDING_EXTREME_SIGNAL`, `QUIET_COMPRESSION_BREAK`

---

## Open Risks

| Risk | Impact | Notes |
|---|---|---|
| Zero signal output cause may be multi-layer | High | Could be evaluator silence + gate rejection + suppression combined |
| Elevated scan latency root cause unknown | High | Could be I/O, pair volume, or data assembly cost |
| Session continuity gap | Medium | This file was created to address this — update it every session end |
| Step 9 tuning requires live data | Medium | No speculative adjustments without diagnostic evidence |

---

## Last Updated

2026-04-11 — PR-09 residual cleanup complete: renamed `pr09_below50` suppression counter to `score_below50` for operator clarity; updated stale "deferred to PR-04" comment in `ACTIVE_PATH_PORTFOLIO_ROLES` and matching test to document that auxiliary channel sub-evaluators are intentionally absent from portfolio-role entries; annotated `OPENING_RANGE_BREAKOUT` as disabled-by-default pending rebuild; replaced all "PR09" log-message prefixes and "PR09 composite engine" comment references with cleaner "scoring"/"composite scoring engine" terminology. Pre-redeploy correction roadmap (PR-01 through PR-09) is now complete.
