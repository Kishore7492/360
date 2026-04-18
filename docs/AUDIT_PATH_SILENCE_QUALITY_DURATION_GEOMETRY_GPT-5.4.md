# AUDIT_PATH_SILENCE_QUALITY_DURATION_GEOMETRY — GPT-5.4

**Model tag:** GPT-5.4  
**Repository:** `mkmk749278/360-v2`  
**Audit mode:** truth-first, evidence-led, code + live-monitor synthesis  
**Date (UTC):** 2026-04-18

---

## 1) Executive verdict

Live expression is currently concentrated in `TREND_PULLBACK_EMA` and `SR_FLIP_RETEST` mainly because they are the two paths that most consistently survive the current funnel stack (generation strictness + MTF gate + geometry/risk-plan gate + post-penalty score/tier + router rules), not because they are clearly the best-performing theses.

The other paths are silent for three different reasons:
1. **by design** (disabled rollout paths and ORB hard-disabled),
2. **pre-scoring attrition** (strict evaluator predicates and family-mismatched MTF behavior),
3. **post-scoring attrition** (WATCHLIST routing, score-below-50, confidence floors, spread/quiet suppression).

The two expressive paths are still weak in live quality because surviving setups are frequently **late/fragile entries with tight realized invalidation distance after risk-plan normalization/capping and heavy suppressor pressure**, producing many fast SL outcomes.

The “~3 minute close” pattern is **both real and an artifact**:
- real: many trades fail almost immediately once SL/TP evaluation becomes eligible,
- artifact: lifecycle has a hard 180s minimum lifespan and 5s polling cadence, while monitor displays round/floor duration into coarse minute buckets.

So the system is currently favoring **survivability under current gates** more than **true setup quality optimality**. The strongest corrections are narrow: targeted MTF semantics for reclaim/reversal, reclaim-family geometry/risk-plan friction reduction, and lifecycle truth telemetry disambiguation. No blanket threshold loosening is needed.

---

## 2) What is actually happening live

Runtime truth from `monitor/latest.txt` and code:
- Live history currently contains only `TREND_PULLBACK_EMA` and `SR_FLIP_RETEST` (`28` total records: `17` + `11`).
- Monitor suppressor summaries repeatedly show:
  - `mtf_gate:360_SCALP`, `mtf_gate_family:360_SCALP:reclaim_retest`, `mtf_gate_setup:...:SR_FLIP_RETEST`, `...:FAILED_AUCTION_RECLAIM`
  - `geometry_rejected_risk_plan:360_SCALP:reclaim_retest`
  - `pair_quality:spread too wide`
  - `QUIET_SCALP_BLOCK`
- Reversal path (`LIQUIDITY_SWEEP_REVERSAL`) is often reaching scoring, but largely landing in `50–64` (WATCHLIST) or being blocked by `trend_hard_gate`, spread suppression, or MTF; it is not becoming durable active live outcomes.
- Geometry warnings are frequent and repetitive (`SL capped ... 1.96/2.09/2.40/2.80% > 1.50%`, `SL near-zero rejection ... < 0.05%`).
- Recent SL follow-through snapshot shows many very short holds (`3m` dominant) and very low MFE before stop.

---

## 3) Path-by-path survival matrix

Scope: active internal `360_SCALP` evaluator paths (`src/channels/scalp.py` evaluate list).

| Path | Generation status | Main gate losses | Score/tier losses | Geometry losses | Routing/lifecycle outcome status |
|---|---|---|---|---|---|
| LIQUIDITY_SWEEP_REVERSAL | **Active generation** (seen in `candidate_reached_scoring`) | MTF family/setup suppression for reversal still present; trend hard gate hits observed | Often `50–64` (WATCHLIST), some `65–79` | Risk-plan often changed (not mostly rejected) | Frequently not emitted to active lifecycle due WATCHLIST/arbitration/suppressors |
| TREND_PULLBACK_EMA | **Active generation** (implied by dominant live emissions/history) | Generic MTF strictness (no family cap), spread suppression, quiet floor | Can still be penalized post-score | Some capped/tight outcomes downstream | Dominant emitter; quality weak (many SL_HIT, short holds) |
| SR_FLIP_RETEST | **Active generation** (history + scoring hits) | Strong MTF suppressor pressure (`mtf_gate_setup`) | Mix of `score_65to79`, `score_50to64`, and `score_below50` seen | Heavy `geometry_rejected_risk_plan:...:reclaim_retest` | Emits enough to appear in history but weak quality profile |
| FAILED_AUCTION_RECLAIM | Generated but fragile | Strong MTF suppressor (`mtf_gate_setup`) | Repeated `score_below50` evidence | Shares reclaim-family geometry rejection pressure | Rare/no emission to active history |
| LIQUIDATION_REVERSAL | Very strict generation predicates (cascade + CVD divergence + RSI extreme + zone + vol spike) | Reversal MTF suppression when it appears | Not enough evidence of regular scoring survival | Not dominant issue in observed monitor window | Practically silent |
| WHALE_MOMENTUM | Rare generation (requires whale/delta + strong tick-flow + OBI regime logic) | Quiet hard block in evaluator; MTF generic gate downstream | Soft penalties can compound | Not primary observed blocker | Practically silent |
| VOLUME_SURGE_BREAKOUT | Strict generation (surge + breakout window + pullback geometry + EMA + RSI + SMC/penalty) | MTF strict family (no cap), spread/quiet suppressors | Likely tier attrition under penalties | Can be geometry-capped | Silent/nearly silent |
| BREAKDOWN_SHORT | Mirror of surge breakout with same strictness | MTF strict family (no cap), spread suppressor | Tier attrition likely | Can be geometry-capped | Silent/nearly silent |
| OPENING_RANGE_BREAKOUT | **Hard-disabled** by config flag | N/A | N/A | N/A | Silent by design |
| FUNDING_EXTREME_SIGNAL | Very strict generation + dependency on funding data | Additional downstream gates/penalties | Likely post-score attrition | Not primary observed blocker | Silent/nearly silent |
| QUIET_COMPRESSION_BREAK | Only QUIET/RANGING + strict squeeze/volume/MACD/SMC conditions | Exempt from quiet block, but still spread/score pressure | Likely score attrition | Not dominant in observed logs | Silent/nearly silent |
| DIVERGENCE_CONTINUATION | Strict divergence/trend/SMC conditions | Generic MTF + spread suppressor | Likely score/tier attrition | Not dominant observed blocker | Silent/nearly silent |
| CONTINUATION_LIQUIDITY_SWEEP | Strict trend+sweep+reclaim structure | Family MTF cap exists but still reversal/continuation suppressors present | Tier attrition frequent for related continuation/reversal styles | Some geometry friction possible | Silent/nearly silent |
| POST_DISPLACEMENT_CONTINUATION | Strict displacement/consolidation/reacceleration structure | MTF + spread + scoring attrition likely | Post-penalty tier compression likely | Protected geometry still can cap/reject | Silent/nearly silent |

Important additional live-path constraint:
- Auxiliary channels are rollout-disabled/radar-only by policy defaults (`360_SCALP_FVG`, `ORDERBLOCK`, etc.), so they cannot contribute paid live emissions currently.

---

## 4) Root causes of silent paths

### A. Correct protective filtering (should remain)
- ORB disabled by doctrine (`SCALP_ORB_ENABLED=false`) pending rebuild.
- Disabled/radar-only rollout states for specialist auxiliary channels.
- Hard invalid geometry checks: wrong-side SL/TP, non-finite, excessive SL distance, near-zero SL.
- Pair spread quality suppression in poor execution conditions.
- Quiet-regime protection for low-confidence scalp noise.

### B. Incorrect or misaligned suppression (high-confidence)
1. **MTF policy is only threshold-capped, not family-semantic**: reclaim/reversal paths still judged by generic EMA-style multi-TF confluence; telemetry shows high `mtf_policy_relaxed` but low `mtf_policy_saved`.
2. **Reclaim-family geometry friction is too dominant**: repeated `geometry_rejected_risk_plan:...:reclaim_retest` indicates many structurally valid evaluator setups do not survive risk-plan normalization.
3. **WATCHLIST trap + routing split**: many candidates survive to scoring but land `50–64`; router intentionally keeps them out of active lifecycle, creating “silent” paid-path behavior.
4. **Survival bias via arbitration**: per-direction arbitration keeps only top confidence candidate, so lower-scoring but possibly cleaner thesis setups are dropped without explicit path-level arbitration telemetry.

---

## 5) Root causes of weak quality on the two expressive paths

For `TREND_PULLBACK_EMA` and `SR_FLIP_RETEST`, weak live quality is a combination of:
- **Entry timing fragility** under strict confluence and penalties (late entries, little immediate excursion).
- **Geometry compression/capping effects** (especially in reclaim-family and micro-price symbols), increasing fast-stop susceptibility.
- **Regime/suppressor mismatch pressure** (MTF + spread + quiet/penalty stack) selecting “policy-survivors” rather than highest edge setups.
- **Scoring/tier compression post-penalty** narrowing the emitted subset to paths that clear all downstream constraints, not necessarily highest expected path quality.

Evidence pattern: many SLs with near-zero MFE, repeated short holds, repeated geometry cap/near-zero warnings, and suppressor concentration around MTF + reclaim geometry + spread.

---

## 6) 3-minute duration analysis (real behavior vs artifact)

### Real behavior
- Trade monitor blocks SL/TP checks for first **180s** (`MIN_SIGNAL_LIFESPAN_SECONDS[360_SCALP]=180`).
- After that, checks run each **5s** (`MONITOR_POLL_INTERVAL=5.0`).
- Therefore a truly weak trade can fail almost immediately after eligibility (~180–185s wall time), which is genuinely fast failure.

### Reporting/lifecycle artifact
- Stored `hold_duration_sec` uses precise wall time (`utcnow() - sig.timestamp`), but monitor tools format coarse minute text:
  - follow-through table prints `f"{hold_sec/60:.0f}m"` (rounding),
  - content posts often floor to integer minutes (`int(hold_sec // 60)`).
- Net effect: many distinct fast failures in ~180–239s collapse visually to `3m` or nearby bucket labels.

### Conclusion
- The short-duration issue is **both**:
  - a **real rapid-failure pattern** (low MFE, quick SL after eligibility), and
  - a **telemetry presentation compression artifact** (minute rounding/flooring and lifecycle cadence granularity).

Trades can practically die in seconds **after** the minimum-lifespan gate opens, while being reported as roughly “3 minutes”.

---

## 7) Geometry-friction analysis

### Proven protective geometry controls
- Channel cap for `360_SCALP` SL distance: **1.5%**.
- Near-zero SL reject threshold: **0.05%** from entry.
- Directional and R:R sanity checks.

### Runtime evidence
- Recurrent cap events around **1.96% / 2.09% / 2.40% / 2.80%** being forced to 1.50%.
- Repeated near-zero SL rejections.
- Reclaim family repeatedly rejected at risk-plan geometry stage.
- Auxiliary FVG path shows extreme geometry rejects (correct for pathological cases).

### Separation: correct vs over-restrictive
- **Correct**: rejecting extreme FVG geometry and wrong-side/near-zero invalidation cases.
- **Potentially over-restrictive/distortive**: reclaim-family setups that pass evaluator thesis but are dropped after risk-plan geometry normalization/capping before scoring/emission.

Yes, geometry friction remains a major silence contributor for reclaim-family paths.

---

## 8) MTF-policy reality check

- Family-aware MTF currently changes only `min_score` caps by family; it does **not** change MTF semantics.
- Reclaim/reversal setups are still evaluated by generic multi-timeframe EMA alignment behavior.
- Telemetry says the same: high `mtf_policy_relaxed` counts but much smaller `mtf_policy_saved` counts, while `mtf_gate_family/setup` remains high for reclaim/reversal.

Verdict: current relaxed family-aware MTF is **partly cosmetic** in live effect for the problematic families.

---

## 9) Best narrow corrective actions (ordered)

1. **Reclaim/Reversal MTF semantic correction (narrow, family-scoped)**
   - Keep global MTF hard gate, but add family-specific confluence semantics for `reclaim_retest` and `reversal` (not just min-score caps).
   - Goal: stop judging these families as trend-following EMA unanimity setups.

2. **Reclaim-family risk-plan geometry reconciliation**
   - Preserve evaluator structural invalidation intent through risk-plan stage with tighter reclaim-specific handling before cap/reject.
   - Goal: reduce `geometry_rejected_risk_plan:...:reclaim_retest` without weakening global geometry safety.

3. **Duration truth telemetry disambiguation**
   - Add explicit lifecycle timestamps/metrics (eligible-at, first-check-after-eligibility, terminal-detected-at, exact hold-sec) and report them without minute-only compression.
   - Goal: separate real fast failures from presentation artifacts and prevent false diagnostic conclusions.

---

## 10) What should not be changed

- Do **not** globally lower confidence thresholds or disable protective spread/geometry checks.
- Do **not** remove quiet-regime scalp protection wholesale.
- Do **not** widen rollout scope or enable disabled channels as a shortcut to increase count.
- Do **not** remove SL cap/near-zero protections globally; only refine path-specific pre-cap geometry handling where doctrinally justified.

---

## 11) PR recommendations (max 3)

### PR-1: Family-semantic MTF for reclaim/reversal
- **Exact problem:** reclaim/reversal families remain over-suppressed by generic MTF logic despite min-score caps.
- **Exact change:** implement family-specific MTF confluence evaluator for `reclaim_retest` and `reversal`, preserving hard gate but aligning criteria with family thesis.
- **Explicit non-scope:** no global threshold changes, no trend-family relaxation, no router changes.
- **Validation criteria:** lower `mtf_gate_family/setup` for reclaim/reversal; increased `mtf_policy_saved` equivalent efficacy; no broad score-quality drift.

### PR-2: Reclaim-family geometry/risk-plan integrity patch
- **Exact problem:** high reclaim-family geometry rejection before scoring/emission.
- **Exact change:** tighten reclaim-specific risk-plan reconciliation to preserve evaluator structural SL/TP intent prior to cap/reject decisions.
- **Explicit non-scope:** no removal of near-zero, wrong-side, cap, or R:R hard protections globally.
- **Validation criteria:** reduced `geometry_rejected_risk_plan:...:reclaim_retest`; stable risk integrity; improved reclaim path progression to scoring/emission.

### PR-3: Lifecycle duration truth instrumentation
- **Exact problem:** 3-minute collapse in reporting obscures whether failures are immediate post-eligibility or truly longer.
- **Exact change:** add precise duration telemetry fields and monitor output that distinguish eligibility delay, detection cadence, and actual hold duration.
- **Explicit non-scope:** no trading logic change, no SL/TP behavior change.
- **Validation criteria:** operator can segment failures into (pre-eligibility hold, post-eligibility-to-terminal latency, exact terminal age) from logs/monitor without inference.

---

## 12) Confidence / uncertainty

### Proven (high confidence)
- Current paid live history is concentrated in `TREND_PULLBACK_EMA` and `SR_FLIP_RETEST`.
- Reclaim-family suppression is strongly concentrated in MTF + geometry risk-plan stages.
- Reversal path frequently reaches scoring but often lands WATCHLIST/filtered and does not become durable active outcomes.
- 3-minute pattern is structurally linked to 180s lifespan gate + 5s monitor cadence + coarse minute formatting.

### Inferred (medium confidence)
- Some silent families are predominantly generation-sparse due very strict evaluator predicates (not only downstream gates).
- Arbitration contributes to suppressing potentially better non-dominant same-direction candidates, but explicit arbitration-drop telemetry is currently limited.

### Needs runtime confirmation (targeted)
- Per-path generated→gated→scored→filtered→emitted ratios over a broader stable window (not only recent snapshot).
- Post-fix quality shift for reclaim/reversal families (MFE, hold-seconds distribution, SL profile) without quality drift.
- Exact contribution split between geometry rejection and post-score tier compression for each silent family across multiple regimes.

