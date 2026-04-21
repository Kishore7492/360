# 360-v2 Full Audit Report — v2 + Live Runtime Data
**Date:** 2026-04-21  
**Codebase:** Post-PR zip v2  
**Runtime window:** ~4 hours post stats-reset  
**Total scan cycles:** 66,122 per evaluator  
**Signal monitor:** truth_snapshot.json + window_comparison.json  

---

## 1. Executive Summary

The monitoring pipeline is now working. For the first time this audit has real runtime data. The picture it reveals is specific and actionable — not "something is wrong" but exactly what is wrong at every stage.

**The system is generating signals but emitting almost none.** In 4 hours: 15,824 evaluator-generated candidates, 8 signals emitted. That is a 99.95% pipeline loss rate. The causes are now fully visible.

**Three findings dominate everything:**

**Finding 1 — FAR is the biggest killer in the system.**  
FAILED_AUCTION_RECLAIM generated 11,283 candidates in 4 hours — far more than any other path. Zero were emitted. 6,273 (56%) were killed by the risk plan because R:R < 1.0. The remaining 5,010 were killed by the confidence gate. FAR is detecting thousands of micro-oscillations that do not constitute genuine failed auctions, and the resulting TP (based on the tiny tail) is smaller than the SL (based on the wick extreme). Fix FAR before doing anything else.

**Finding 2 — 98.4% of scans are in non-trending regime.**  
65,055 of 66,122 scan cycles blocked TREND_PULLBACK, CLS, PDC, and DIVERGENCE_CONTINUATION via regime gate. The market has been QUIET/RANGING for the entire 4-hour window. This is a market condition, not a code bug. But it means the paths that DO fire in RANGING (SR_FLIP, FAR, LSR, QCB) must be in perfect working order — and they are not due to Finding 1.

**Finding 3 — orderblocks are 100% absent.**  
Every single one of the 66,122 scan cycles returned zero orderblocks. This silently affects every path that requires `FVG OR orderblocks`. If FVG is also sparse, multiple paths are being hard-rejected on a dependency that has not populated once.

**Total emissions in 4 hours: 8** (2 LIQUIDITY_SWEEP_REVERSAL, 5 SR_FLIP_RETEST, 1 CONTINUATION_LIQUIDITY_SWEEP).

---

## 2. Live Runtime Funnel — Full Data

### 2.1 Emission funnel by path (4 hours, 66,122 scan cycles)

| Path | Generated | R:R Killed | Gated | Emitted | Status |
|---|---:|---:|---:|---:|---|
| FAILED_AUCTION_RECLAIM | 11,283 | 6,273 (56%) | 11,283 | 0 | 🔴 Critical — R:R collapse |
| SR_FLIP_RETEST | 2,516 | 1,288 (51%) | 2,288 | 5 | 🟡 Working but leaking |
| LIQUIDITY_SWEEP_REVERSAL | 1,857 | 0 | 1,575 | 2 | 🟡 Working, low emission |
| QUIET_COMPRESSION_BREAK | 143 | 100 (70%) | 143 | 0 | 🔴 R:R collapse |
| CONTINUATION_LIQUIDITY_SWEEP | 15 | 2 (13%) | 12 | 1 | 🟢 Generating correctly |
| TREND_PULLBACK_EMA | 8 | 2 (25%) | 6 | 0 | 🟡 Low volume, regime-blocked |
| POST_DISPLACEMENT_CONTINUATION | 1 | 0 | 1 | 0 | 🟡 Low volume |
| BREAKDOWN_SHORT | 1 | 1 (100%) | 1 | 0 | 🔴 R:R |
| WHALE_MOMENTUM | 0 | — | — | 0 | 🔴 Non-generating (no whale data) |
| VOLUME_SURGE_BREAKOUT | 0 | — | — | 0 | 🔴 Non-generating (no surges) |
| DIVERGENCE_CONTINUATION | 0 | — | — | 0 | 🟡 Regime-blocked (98.4%) |
| LIQUIDATION_REVERSAL | 0 | — | — | 0 | 🟡 No cascade events |
| FUNDING_EXTREME | 0 | — | — | 0 | 🟡 Funding not extreme |
| OPENING_RANGE_BREAKOUT | 0 | — | — | 0 | ✅ Correctly disabled |

### 2.2 Scanner gate summary (post-evaluator)

For signals that DO reach the scanner after the evaluator generates them:

| Path | Generated | Risk Plan Pass | Scored | Filtered | Emitted |
|---|---:|---:|---:|---:|---:|
| LIQUIDITY_SWEEP_REVERSAL | 1,857 | ~1,857 (adj/capped) | 282 | 280 | 2 |
| SR_FLIP_RETEST | 2,516 | ~1,228 | 228 | 223 | 5 |
| FAILED_AUCTION_RECLAIM | 11,283 | ~5,010 | 0 | 0 | 0 |
| QUIET_COMPRESSION_BREAK | 143 | ~43 | 0 | 0 | 0 |
| TREND_PULLBACK_EMA | 8 | ~6 | 2 | 2 | 0 |
| CLS | 15 | ~13 | 3 | 2 | 1 |

**The confidence gate is the second largest killer after R:R.** LIQUIDITY_SWEEP_REVERSAL: 282 scored → 280 filtered. SR_FLIP: 228 scored → 223 filtered. Nearly everything that survives geometry is then killed by confidence scoring.

---

## 3. Per-Path Analysis — With Live Data

### FAILED_AUCTION_RECLAIM — Critical Priority

**Numbers:** 11,283 generated → 6,273 R:R killed → 5,010 reach confidence gate → 0 emitted

**Root cause of R:R collapse:**  
FAR computes TP1 based on `tail * 1.0` where `tail = reclaim_level - auction_wick_extreme`. When the failed auction probe is shallow (price only barely breached the reference level), the tail is tiny — sometimes 2–5 ticks. The SL is placed at `auction_wick_extreme - atr*0.3`, which is further away than the tiny tail. Result: R:R = tiny_tail / (tiny_tail + atr*0.3) << 1.0.

The R:R breakdown from the raw data shows rejections from rr_0.01 all the way up to rr_0.50 — meaning the majority of FAR candidates have R:R between 0.01 and 0.50. This is structural, not random.

**Root cause of over-detection:**  
FAR's `_FAR_ACCEPTANCE_THRESHOLD = 0.002` (0.2%) allows any bar whose low was within 0.2% of the reference level to qualify as a "failed acceptance." On a 5m chart with ATR around 0.3–0.5%, a 0.2% probe barely exceeds normal price noise. This setting causes FAR to fire on thousands of micro-oscillations that are not genuine structural rejections.

**Fix required:**  
Two changes needed in `_evaluate_failed_auction_reclaim()`:

1. Raise `_FAR_ACCEPTANCE_THRESHOLD` from 0.002 to 0.001 (require the auction candle to close within 0.1% of the level, not 0.2%) — makes the failed acceptance test stricter.

2. Add a minimum tail requirement before entering the signal path:
```python
# Minimum tail as fraction of ATR — prevents trivial micro-probes
_FAR_MIN_TAIL_ATR = 0.3  # tail must be at least 0.3× ATR

tail = reclaim_level - auction_wick_extreme  # LONG case
if tail < atr_val * _FAR_MIN_TAIL_ATR:
    return self._reject("tail_too_small")
```

3. Add a TP floor based on minimum viable R:R:
```python
# Ensure TP1 is at least 1.0R from entry
min_tp1_dist = sl_dist * 1.0
if direction == Direction.LONG:
    tp1 = max(close + tail * 1.0, close + min_tp1_dist)
else:
    tp1 = min(close - tail * 1.0, close - min_tp1_dist)
```

**Expected impact:** FAR generations will drop from 11,283 to perhaps 200–500. But those 200–500 will have genuine tail depth and viable R:R, so they will pass risk plan. This is the single most important fix in the current codebase.

---

### SR_FLIP_RETEST — Working But Leaking

**Numbers:** 2,516 generated → 1,288 R:R killed (51%) → 228 survive → 5 emitted

SR_FLIP is working — it is the top-emitting path with 5 signals. But 51% of generated candidates fail R:R. The rejection reasons cluster in the rr_0.19–0.84 range, suggesting the SL is consistently wider than TP1.

**Root cause:** SR_FLIP uses a complex SL formula:
```
invalidation_anchor = min(level, last_low)  # LONG
sl = invalidation_anchor - invalidation_buffer  # where buffer = max(level_buffer, atr_buffer, structural_buffer)
```

The structural failure buffer (`wick_overshoot + atr_val * 0.15`) can be large when the wick overshot the level significantly. Meanwhile TP1 is the 20-bar swing high, which may be close to current price.

**Fix:** The SL placement logic is structurally correct — the SL should be at true invalidation. The issue is TP1 being too close. Replace the 20-bar lookback TP1 with a minimum guaranteed R:R fallback when the structural level is too close:

```python
# After computing tp1 from swing high:
min_tp1 = close + sl_dist * 1.2 if direction == Direction.LONG else close - sl_dist * 1.2
if direction == Direction.LONG:
    tp1 = max(tp1, min_tp1)  # ensure at least 1.2R
else:
    tp1 = min(tp1, min_tp1)
```

This ensures SR_FLIP signals have minimum 1.2R before reaching the risk plan.

---

### LIQUIDITY_SWEEP_REVERSAL (STANDARD path) — Telemetry Gap

**Numbers:** 1,857 generated → 2 emitted

The no-signal reason shows `"none": 64,265` — meaning 64,265 rejections have no named reason. The STANDARD path (`_evaluate_standard`) uses bare `return None` in most branches, not `self._reject()`. This makes the rejection funnel completely opaque.

**This is the same problem that was fixed for BREAKDOWN_SHORT (PR-5) but was never applied to the STANDARD path.**

Additionally, the scanner is changing LIQUIDITY_SWEEP_REVERSAL geometry for all 282 scored signals (`geometry:final_live:changed: 282`) and capping 26 (`geometry:risk_plan:capped: 26`). The changed geometry is being scored then filtered (280 filtered vs 2 emitted). This is a sign that geometry is being adjusted but the adjusted geometry still fails confidence scoring.

---

### QUIET_COMPRESSION_BREAK — R:R Below Minimum

**Numbers:** 143 generated → 100 R:R killed (70%) → 0 emitted

QCB requires R:R ≥ 1.2. The rejection codes are:
- `rr_0_32_below_1_20`: 6
- `rr_0_41_below_1_20`: 44
- `rr_0_42_below_1_20`: 50
= 100 rejections, all below 1.2R

In QUIET regime, Bollinger Bands are compressed (that is the trigger condition). The TP is computed from `band_width * 0.5/1.0/1.5`. With narrow bands (< 1.5% of close), TP distances are tiny. Even with the widened SL from PR-9, the R:R can still fall below 1.2.

**Fix:** Add a TP floor for QCB based on minimum R:R:
```python
# Ensure TP1 is at least 1.3× SL distance (leaves buffer above 1.2R minimum)
if direction == Direction.LONG:
    tp1 = max(tp1, close + sl_dist * 1.3)
    tp2 = max(tp2, close + sl_dist * 2.0)
else:
    tp1 = min(tp1, close - sl_dist * 1.3)
    tp2 = min(tp2, close - sl_dist * 2.0)
```

---

### WHALE_MOMENTUM — Structural Data Gap

**Numbers:** 0 generated (non-generating)

Rejection reasons:
- `regime_blocked`: 48,521 (73.4%) — QUIET market
- `momentum_reject`: 17,601 (26.6%) — no whale alert AND no volume_delta_spike

The `momentum_reject` path fires when `whale = smc_data.get("whale_alert")` is None AND `delta_spike = smc_data.get("volume_delta_spike", False)` is False. This is a data supply issue: whale alerts are event-driven external data (Whale Alert API). If the integration is not streaming whale events, this path will never generate regardless of market conditions.

**Check required:** Verify the whale alert integration is active and events are being written to `smc_data["whale_alert"]` during scan cycles. If not, the WHALE_MOMENTUM path is effectively disabled by missing data rather than a code issue.

---

### VOLUME_SURGE_BREAKOUT — Regime and Volume Conditions

**Numbers:** 0 generated (non-generating)

Rejection reasons:
- `regime_blocked`: 48,521 (QUIET)
- `volume_spike_missing`: 11,530 (volume not surging in non-QUIET periods)
- `basic_filters_failed`: 5,159
- `breakout_not_found`: 541

In a QUIET market with no volume surges, this path correctly produces nothing. No code change needed — this is correct behavior. When the market transitions to a trending/volatile regime with volume expansion, this path should begin generating.

---

### DIVERGENCE_CONTINUATION — Correctly Regime-Blocked

**Numbers:** 0 generated

- `regime_blocked`: 65,055 (98.4%)

DIVERGENCE_CONTINUATION only fires in TRENDING_UP or TRENDING_DOWN regimes. The market has been RANGING/QUIET for 98.4% of the window. This is correct behavior. When the market trends, this path will generate.

---

### LIQUIDATION_REVERSAL — No Cascade Events

**Numbers:** 0 generated

- `cascade_threshold_not_met`: 41,150 — no pair moved 2%+ in 3 candles
- `basic_filters_failed`: 23,488
- `cvd_divergence_failed`: 1,444

The market has not produced cascade-level moves in the 4-hour window. The path is correctly gated. When cascades occur, it will fire.

---

### FUNDING_EXTREME — Telemetry Gap + Funding Conditions

**Numbers:** 0 generated

- `"none"`: 48,521 — the QUIET block uses bare `return None`, not `self._reject("regime_blocked")`
- `funding_not_extreme`: 12,065 — funding is within normal range
- `basic_filters_failed`: 5,140
- `rsi_reject`: 54

**Code issue:** The QUIET block in `_evaluate_funding_extreme` is:
```python
if regime_upper == "QUIET":
    return None  # bare return, not self._reject()
```
This creates 48,521 opaque "none" entries in telemetry. Fix: use `return self._reject("regime_blocked")`.

**Market condition:** When funding reaches extreme levels (`> FUNDING_RATE_EXTREME_THRESHOLD`), this path will generate. Normal funding rates correctly produce no signals.

---

### TREND_PULLBACK_EMA — Confirmed Bottleneck

**Numbers:** 8 generated in 4 hours, 0 emitted

Rejection reasons with counts:
- `regime_blocked`: 65,055 (98.4%) — market is RANGING
- `retest_proximity_failed`: 226 — price not near EMA
- `ema_alignment_reject`: 501 — EMAs not aligned
- `rsi_reject`: 94 — **only 94 rejections from RSI gate**
- `momentum_reject`: 115
- `basic_filters_failed`: 46

**Critical insight:** `rsi_reject` accounts for only 94 rejections out of 66,122 attempts. This is 0.14% of total attempts. The PR-12 RSI gate widening was recommended based on the assumption that RSI was blocking many valid setups. The data says this is NOT the primary bottleneck — the real bottleneck is the regime gate (98.4% blocked).

**However:** The regime blockage is a market condition (RANGING). When the market trends, PR-12 RSI widening will matter because the RSI gate will then be one of the active gates. The fix is still correct, just less urgent than expected from the data so far.

The 2 TREND_PULLBACK signals that survived to `scored` were both `geometry:risk_plan:rejected` (too tight SL distance). This is the same TP/SL issue.

---

## 4. Dependency Readiness Analysis

### 4.1 Dependency health table

| Dependency | Populated | Empty/Absent | Issue Level |
|---|---:|---:|---|
| CVD | 100.0% (66,099) | 0.03% (23) | ✅ None |
| Recent Ticks | 96.4% (63,763) | 3.6% (2,359) | ✅ Minor |
| OI Snapshot | 99.2% (65,620) | 0.8% (502) | ✅ Minor |
| Funding Rate | 99.2% (65,613) | 0.8% (509) | ✅ Minor |
| Order Book | 86.4% present | 13.6% unavailable | 🟡 Quality: 100% top-of-book only |
| Liquidation Clusters | 45.6% (30,153) | 54.4% (35,969) | 🔴 Critical |
| Orderblocks | 0.0% (0) | 100.0% (66,122) | 🔴 Critical |

### 4.2 Orderblocks — 100% absent (Critical)

Every single scan cycle returns zero orderblocks. This has never populated once in 4 hours.

**Affected paths:**
- TREND_PULLBACK: requires `fvg OR orderblocks` — if FVG is also sparse, hard-blocked
- DIVERGENCE_CONTINUATION: same requirement
- QUIET_COMPRESSION_BREAK: same requirement
- SR_FLIP_RETEST (fast regimes): uses orderblocks as soft FVG fallback

**Root cause candidates:**
1. The SMC orderblock detector is not being called, or its output is not being written to `smc_data["orderblocks"]`
2. The detector runs but finds no qualifying orderblocks under its criteria (body ratio ≥ 60%, volume ≥ 1.5× ATR)
3. The `smc_data` key is present but always empty (`[]`)

**Required investigation:** Check the SMC detector's orderblock output in a live scan cycle. Confirm whether `smc_data["orderblocks"]` is populated at all before the channel evaluation step. If the detector is running and finding nothing, the detection criteria may be too strict.

### 4.3 Liquidation Clusters — 54.4% absent

More than half of scans have no liquidation cluster data. This directly impacts:
- **FUNDING_EXTREME SL:** Falls back to ATR×1.5 in 54.4% of cases (flagged correctly via `LIQ_CLUSTER_ABSENT` per PR-11)
- **Any path using liquidation context for confirmation** — the data simply is not there

This is likely a data pipeline issue: liquidation events are not being persisted between scans, or the cluster detection window is too narrow.

### 4.4 Order Book — 100% top-of-book only

All 57,146 present order book entries are from `book_ticker` (top-of-book only, not full depth). Zero scans have full depth order book data.

**Impact on WHALE_MOMENTUM:** The OBI check requires full depth. With book_ticker only, it applies a `obi_penalty = max(obi_penalty, 10.0)` and sets `obi_confirmed = False`. Any WHALE signal (if it did generate) would start with -10 confidence from the OBI penalty alone.

**Recommendation:** If the full-depth WebSocket stream for order book is not connecting, WHALE_MOMENTUM's OBI requirement is functionally impossible to satisfy. Verify the depth stream is active.

---

## 5. Regime Distribution — Market Context

The regime distribution in the 4-hour window reveals a strongly QUIET/RANGING market:

| Regime Pattern | Scan Cycles | % of Total |
|---|---:|---:|
| QUIET/RANGING (blocks all trending paths) | ~65,055 | 98.4% |
| QUIET specifically (blocks WHALE/SURGE/BREAKDOWN) | ~48,521 | 73.4% |
| VOLATILE or STRONG_TREND (blocks SR_FLIP, FAR) | ~10,415 | 15.8% |
| Trending regimes (TRENDING_UP/DOWN) | ~1,067 | 1.6% |

**What this means:** For 4 hours, the market has been almost entirely RANGING or QUIET. This is the primary reason most paths generated nothing. It is NOT a bug — the regime gates are working correctly. But it creates a dependency problem: the paths that DO fire in RANGING (SR_FLIP, FAR, LSR) must be in perfect working order, and they are being massacred by R:R issues.

When the market transitions to a trending or volatile state, many paths will begin generating. The R:R and telemetry fixes must be in place before that transition.

---

## 6. PR Status — Updated

### Previously Implemented (confirmed correct)

| PR | Status | Confirmed By |
|---|---|---|
| PR-1: Exception isolation | ✅ Done | 14 evaluators all reporting individually in telemetry |
| PR-2: smc_data mutation removed | ✅ Done | No cross-contamination in evaluator counts |
| PR-3: Signal fields declared | ✅ Done | No AttributeError exceptions in telemetry |
| PR-4: VWAP + Ichimoku disabled | ✅ Done | Zero SVWP/SICH signals in funnel |
| PR-5: BREAKDOWN_SHORT telemetry | ✅ Done | All 6 failure reasons visible: regime_blocked, basic_filters_failed, etc. |
| PR-6: CLS sweep tokens + FE SL flag | ✅ Done | `sweeps_not_detected` visible in CLS reasons |
| PR-7 (partial): DIV_CONT TP split | ⚠️ Partial | No guard `tp2 > tp1` — still needed |
| PR-8: CLS sweep.index tokens | ✅ Done | Token names active in telemetry |
| PR-9: QCB SL widened | ✅ Done | QCB now generating 143 (was 0) |
| PR-11: FE SL hierarchy | ✅ Done | `LIQ_CLUSTER_ABSENT` visible |

### Not yet implemented

| PR | Status | Impact |
|---|---|---|
| PR-10: VOLUME_SURGE/BREAKDOWN TP cap | ❌ Not done | Low urgency while market is QUIET |
| PR-12: TREND_PULLBACK RSI widening | ❌ Not done | RSI blocks only 94 cycles; regime is dominant |
| PR-FIX-7B: DIV_CONT TP2 > TP1 guard | ❌ Not done | Low urgency while regime-blocked 98.4% |

---

## 7. New Issues Found From Live Data

### NEW-1 — FAR minimum tail threshold (Critical)
As detailed above. 11,283 micro-auctions generated, all killed by R:R. FAR needs a minimum tail distance requirement and a TP floor.

### NEW-2 — SR_FLIP TP1 minimum R:R floor (High)
1,288 SR_FLIP signals killed by R:R. TP1 from 20-bar swing high is too close when the flip just happened. Add minimum R:R 1.2 floor to TP1.

### NEW-3 — QCB TP minimum R:R floor (High)
100/143 QCB signals killed by R:R < 1.2. Band-width-based TPs are too small in compressed conditions. Add R:R floor to TP1.

### NEW-4 — STANDARD path (LSR) bare return None telemetry gap (High)
64,265 rejections show as `"none"`. The `_evaluate_standard` path was never updated to use `self._reject()`. Cannot diagnose what is blocking LSR signals.

### NEW-5 — FUNDING_EXTREME QUIET block uses bare return None (Medium)
48,521 FUNDING_EXTREME rejections show as `"none"` because the QUIET block uses `return None` not `self._reject("regime_blocked")`. Minor but makes the telemetry table misleading.

### NEW-6 — Orderblocks 100% absent — SMC detector issue (Critical)
Zero orderblocks across 66,122 scans. Needs investigation: is the orderblock detector running? Is it writing to `smc_data["orderblocks"]`?

### NEW-7 — Confidence gate is second largest killer (High)
After geometry, the confidence gate kills the vast majority of remaining signals. LIQUIDITY_SWEEP_REVERSAL: 282 scored → 280 filtered. SR_FLIP: 228 scored → 223 filtered. The minimum confidence threshold (default 65%) combined with soft penalties is eliminating nearly everything that passes geometry. This requires investigation once R:R issues are fixed, to understand whether the confidence gate is correctly identifying weak signals or over-filtering.

### NEW-8 — WHALE_MOMENTUM data supply gap (Medium)
17,601 rejections from `momentum_reject` (no whale alert AND no delta spike). Verify the whale alert integration is actively writing to `smc_data["whale_alert"]`.

---

## 8. Complete PR Roadmap — Prioritized By Impact

### Phase 0 — Maximum signal impact, implement immediately

---

#### PR-NEW-1: FAR Minimum Tail Threshold + TP Floor
**Priority:** Critical  
**Expected impact:** Eliminates 10,000+ phantom R:R rejections; enables FAR to emit  
**Risk:** Low — strictly tightens detection quality

**File:** `src/channels/scalp.py`

**Step 1 — Add module-level constant:**
```python
# FAILED_AUCTION_RECLAIM constants (add near existing FAR constants)
_FAR_MIN_TAIL_ATR: float = 0.30   # tail must be at least 0.3× ATR
_FAR_MIN_RR: float = 1.0          # guaranteed minimum R:R at TP1
```

**Step 2 — In `_evaluate_failed_auction_reclaim()`, after determining direction and before the RSI gate, add:**
```python
# Compute tail depth before proceeding
if direction == Direction.LONG:
    tail = reclaim_level - auction_wick_extreme
else:
    tail = auction_wick_extreme - reclaim_level

# Reject micro-probes where the tail is too small to produce viable R:R
if tail < atr_val * _FAR_MIN_TAIL_ATR:
    return self._reject("tail_too_small")
```

**Step 3 — Replace TP computation with R:R-floored version:**
```python
# TP: measured move from failed-auction tail, with minimum R:R floor
if direction == Direction.LONG:
    tp1_tail = close + tail * 1.0
    tp1_rr = close + sl_dist * _FAR_MIN_RR  # minimum 1.0R
    tp1 = max(tp1_tail, tp1_rr)             # take whichever is further
    tp2 = close + tail * 1.5
    tp3 = close + tail * 2.5
else:
    tp1_tail = close - tail * 1.0
    tp1_rr = close - sl_dist * _FAR_MIN_RR
    tp1 = min(tp1_tail, tp1_rr)
    tp2 = close - tail * 1.5
    tp3 = close - tail * 2.5

# Existing fallbacks for tp2/tp3 below entry:
if direction == Direction.LONG and tp2 <= tp1:
    tp2 = close + sl_dist * 2.5
if direction == Direction.SHORT and tp2 >= tp1:
    tp2 = close - sl_dist * 2.5
```

**Also tighten `_FAR_ACCEPTANCE_THRESHOLD`:**
```python
# BEFORE: _FAR_ACCEPTANCE_THRESHOLD: float = 0.002
# AFTER:
_FAR_ACCEPTANCE_THRESHOLD: float = 0.001  # 0.1% close proximity — stricter
```

**Validation:**
- Assert `sig.tp1 - sig.entry >= sig.entry - sig.stop_loss` (LONG case) — TP1 must be at least 1.0R
- Assert `self._reject` called with "tail_too_small" when tail < 0.3× ATR
- Monitor: FAR generation count should drop by ~85%. FAR emission should begin.

---

#### PR-NEW-2: SR_FLIP TP1 Minimum R:R Floor
**Priority:** High  
**Expected impact:** Reduces 1,288 R:R rejections; increases SR_FLIP emission rate  
**Risk:** Low

**File:** `src/channels/scalp.py` — `_evaluate_sr_flip_retest()`

After computing tp1 from 20-bar swing high, add minimum R:R floor:
```python
# Current:
if direction == Direction.LONG:
    tp1 = max(float(h) for h in highs[-21:-1]) if len(highs) >= 21 else 0.0
    if tp1 <= close:
        tp1 = close + sl_dist * 1.5

# Add after:
    # Ensure minimum 1.2R regardless of swing high position
    min_tp1 = close + sl_dist * 1.2
    tp1 = max(tp1, min_tp1)

else:  # SHORT
    tp1 = min(float(low_val) for low_val in lows[-21:-1]) if len(lows) >= 21 else 0.0
    if tp1 >= close:
        tp1 = close - sl_dist * 1.5
    # Add:
    min_tp1 = close - sl_dist * 1.2
    tp1 = min(tp1, min_tp1)
```

**Validation:** Assert `(sig.tp1 - sig.entry) / (sig.entry - sig.stop_loss) >= 1.2` for LONG signals.

---

#### PR-NEW-3: QCB TP Minimum R:R Floor
**Priority:** High  
**Expected impact:** Eliminates 100 R:R rejections; enables QCB to emit  
**Risk:** Low

**File:** `src/channels/scalp.py` — `_evaluate_quiet_compression_break()`

After computing band-width-based TPs, add floor:
```python
# After existing TP computation, before build_channel_signal():
_min_tp1_dist = sl_dist * 1.3  # Target 1.3R to clear 1.2R minimum
_min_tp2_dist = sl_dist * 2.0
if direction == Direction.LONG:
    tp1 = max(tp1, close + _min_tp1_dist)
    tp2 = max(tp2, close + _min_tp2_dist)
    tp3 = max(tp3, close + sl_dist * 3.0)
else:
    tp1 = min(tp1, close - _min_tp1_dist)
    tp2 = min(tp2, close - _min_tp2_dist)
    tp3 = min(tp3, close - sl_dist * 3.0)
```

**Validation:** Assert all QCB signals have R:R ≥ 1.2 in the risk plan.

---

#### PR-NEW-4: STANDARD Path Telemetry (LSR bare return None)
**Priority:** High  
**Expected impact:** Makes 64,265 opaque rejections visible; enables LSR diagnosis  
**Risk:** Very low — telemetry only

**File:** `src/channels/scalp.py` — `_evaluate_standard()`

Replace all bare `return None` with `return self._reject("reason")`:

| Current | Replace with |
|---|---|
| `return None` after m5 check | `return self._reject("insufficient_candles")` |
| `return None` after adx check | `return self._reject("adx_reject")` |
| `return None` after basic_filters | `return self._reject("basic_filters_failed")` |
| `return None` after ema check | `return self._reject("ema_alignment_reject")` |
| `return None` after sweeps check | `return self._reject("sweeps_not_detected")` |
| `return None` after mom is None | `return self._reject("momentum_reject")` |
| `return None` after momentum threshold | `return self._reject("momentum_reject")` |
| `return None` after persistence check | `return self._reject("momentum_reject")` |
| `return None` after RSI check | `return self._reject("rsi_reject")` |
| `return None` after direction/momentum | `return self._reject("momentum_reject")` |
| `return None` after EMA alignment | `return self._reject("ema_alignment_reject")` |
| `return None` after MACD | `return self._reject("macd_reject")` |
| `return None` after MTF gate | `return self._reject("mtf_reject")` |
| `return None` after HTF EMA gate | `return self._reject("htf_ema_reject")` |
| `return None` after sl geometry | `return self._reject("invalid_sl_geometry")` |

**Validation:** The `no_signal_reasons` for STANDARD must show specific reasons instead of `"none": 64265`.

---

#### PR-NEW-5: FUNDING_EXTREME QUIET Block Telemetry
**Priority:** Medium  
**Expected impact:** Removes 48,521 misleading "none" entries from FUNDING_EXTREME telemetry  
**Risk:** Very low

**File:** `src/channels/scalp.py` — `_evaluate_funding_extreme()`

```python
# BEFORE:
if regime_upper == "QUIET":
    return None

# AFTER:
if regime_upper == "QUIET":
    return self._reject("regime_blocked")
```

---

### Phase 1 — Dependency investigation

---

#### PR-NEW-6: Investigate and Fix Orderblock Detector
**Priority:** Critical investigation  
**Type:** Investigation → fix (code location TBD)  
**Risk:** Medium (requires understanding SMC detector internals)

**Investigation steps:**

1. Add a debug log to the SMC detector's orderblock output:
```python
# In smc.py or wherever orderblocks are detected:
log.debug("SMC orderblocks for {}: {} found", symbol, len(orderblocks))
```

2. Check whether `smc_data["orderblocks"]` is being populated at all before channel evaluation:
```python
# In scanner/__init__.py, in _build_scan_context():
_ob_count = len(smc_data.get("orderblocks", []))
if _ob_count == 0:
    log.debug("orderblocks empty for {} — zero detected", symbol)
```

3. If the detector runs but finds nothing: the detection criteria in `scalp_orderblock.py` requires:
   - `body / range >= 0.60` (strong directional body)
   - `range >= atr * 1.5` (impulse size)
   
   Consider whether these thresholds are too strict for current market conditions.

4. If the detector is not running: check whether `smc_data["orderblocks"]` is populated by the SMC detector or by the ScalpOrderblockChannel. If the latter, the key may only be set when ScalpOrderblockChannel is called, not globally.

**This is the most important investigation because 100% orderblock absence may be silently blocking paths that require `fvg OR orderblocks`.**

---

#### PR-NEW-7: Investigate Confidence Gate Kill Rate
**Priority:** High investigation (after R:R fixes)  
**Type:** Investigation first  

After PR-NEW-1 through PR-NEW-3 are deployed:
- FAR should begin emitting
- QCB should begin emitting
- SR_FLIP emission should increase

At that point, run the VPS monitor again. If signals are still being killed by the confidence gate at high rates (observe: scored → filtered ratio), investigate:

1. What is the default minimum confidence threshold? (`MIN_CONFIDENCE_THRESHOLD` or equivalent in config)
2. What do the `component_scores` look like for signals that survive geometry but are then filtered?
3. Are soft penalties (accumulated from all evaluators) being deducted correctly?

Do NOT lower the confidence threshold blindly. Understand what components are driving low scores first.

---

### Phase 2 — Complete remaining code PRs

---

#### PR-10: Cap VOLUME_SURGE + BREAKDOWN TP
**Priority:** Low-Medium (not firing currently due to QUIET regime)  
**When:** After Phase 0 is deployed and market transitions

**File:** `src/channels/scalp.py` — both volume paths

```python
# Add after measured_move computation in both _evaluate_volume_surge_breakout
# and _evaluate_breakdown_short:
_SCALP_TP_MAX_MULT = 3.0
if measured_move > sl_dist * _SCALP_TP_MAX_MULT:
    measured_move = sl_dist * _SCALP_TP_MAX_MULT
```

---

#### PR-12: Widen TREND_PULLBACK RSI Gate
**Priority:** Low (RSI only accounts for 94 rejections; regime is dominant)  
**When:** After market transitions to trending; monitor RSI rejection counts then

```python
# In _evaluate_trend_pullback():
# BEFORE:
if rsi_val is not None and not (40 <= rsi_val <= 60):
    return self._reject("rsi_reject")

# AFTER:
rsi_penalty = 0.0
if rsi_val is not None:
    if not (35 <= rsi_val <= 65):
        return self._reject("rsi_reject")
    if rsi_val < 40 or rsi_val > 60:
        rsi_penalty = 4.0
```

Also remove the `rsi_prev` direction check (adds 115 momentum_reject counts):
```python
# REMOVE:
# rsi_prev = ind.get("rsi_prev")
# if rsi_val is not None and rsi_prev is not None:
#     if direction == Direction.LONG and float(rsi_val) <= float(rsi_prev): ...
```

---

#### PR-FIX-7B: DIV_CONT TP2 > TP1 Guard
**Priority:** Low (98.4% regime-blocked currently)  
**When:** After Phase 0

```python
# In _evaluate_divergence_continuation(), after computing both TPs:
if direction == Direction.LONG and tp2 <= tp1:
    tp2 = close + sl_dist * 2.5
if direction == Direction.SHORT and tp2 >= tp1:
    tp2 = close - sl_dist * 2.5
```

---

### Phase 3 — Quality and tuning (after Phase 0+1 stable)

- PR-13: TREND_PULLBACK quality gate telemetry
- PR-14: LIQUIDATION_REVERSAL RSI gate widening (confirm cascade events are occurring first)
- PR-15: QCB TP degenerate band width minimum

---

## 9. Do Not Do List

| Temptation | Why Not |
|---|---|
| Lower minimum confidence threshold | You don't yet know what's driving low confidence. Fix R:R issues first, then audit component scores. Lowering the threshold emits lower quality signals, not more correct ones. |
| Add new paths | 14 paths exist. 5 are non-generating. Fix the existing ones before adding more. |
| Tune ADX thresholds | ADX reject is minor (190 counts for CLS/PDC). Not a bottleneck. |
| Re-enable VWAP or Ichimoku | Both correctly disabled. Rolling VWAP is structurally wrong. 5m Ichimoku is wrong. |
| Adjust regime thresholds | Regime distribution is a market condition. The market IS ranging. The system is correctly identifying this. |
| Enable OPENING_RANGE_BREAKOUT | 100% regime-blocked. Even if enabled, the proxy logic (last 8 bars) is not real ORB. |
| Tune soft penalty weights | Cannot meaningfully tune confidence weighting until R:R and telemetry issues are fixed. |
| Widen FAR detection threshold | `_FAR_ACCEPTANCE_THRESHOLD` should be TIGHTENED from 0.002 to 0.001, not widened. The path is over-detecting, not under-detecting. |

---

## 10. Summary Checklist

### Fix immediately (Phase 0 — highest signal impact)
- [ ] **PR-NEW-1:** FAR minimum tail threshold + TP floor ← single biggest expected impact
- [ ] **PR-NEW-2:** SR_FLIP TP1 minimum 1.2R floor
- [ ] **PR-NEW-3:** QCB TP minimum 1.3R floor
- [ ] **PR-NEW-4:** STANDARD path (LSR) telemetry — replace bare return None
- [ ] **PR-NEW-5:** FUNDING_EXTREME QUIET block telemetry fix

### Investigate urgently (Phase 1)
- [ ] **PR-NEW-6:** Why are orderblocks 100% absent? Trace SMC detector output.
- [ ] **PR-NEW-7:** After R:R fixes, read confidence gate kill rate from new monitor run

### Complete code PRs (Phase 2)
- [ ] **PR-10:** VOLUME_SURGE + BREAKDOWN TP cap
- [ ] **PR-12:** TREND_PULLBACK RSI gate widen
- [ ] **PR-FIX-7B:** DIV_CONT TP2 > TP1 guard

### Previously complete — do not revisit
- [x] PR-1: Exception isolation
- [x] PR-2: smc_data mutation removed
- [x] PR-3: Signal fields declared
- [x] PR-4: VWAP + Ichimoku disabled
- [x] PR-5: BREAKDOWN_SHORT telemetry
- [x] PR-6: CLS sweep tokens + FE SL flag
- [x] PR-8: CLS sweep.index tokens
- [x] PR-9: QCB SL widened
- [x] PR-11: FE SL hierarchy

---

## 11. Expected Outcome After Phase 0

If PR-NEW-1 through PR-NEW-5 are deployed and the market remains RANGING:

| Path | Current Emissions | Expected After |
|---|---:|---|
| FAILED_AUCTION_RECLAIM | 0 / 4h | 5–20 / 4h (genuine auctions with R:R ≥ 1.0) |
| SR_FLIP_RETEST | 5 / 4h | 10–20 / 4h (more survive R:R gate) |
| QUIET_COMPRESSION_BREAK | 0 / 4h | 2–8 / 4h (R:R floor enables emission) |
| LIQUIDITY_SWEEP_REVERSAL | 2 / 4h | 2–4 / 4h (telemetry fix reveals true gate) |
| Other paths | unchanged | unchanged (regime-dependent) |

**Total expected:** ~20–50 signals per 4 hours in RANGING regime (vs current 8).

When the market transitions to trending: TREND_PULLBACK, CLS, PDC, DIVERGENCE_CONTINUATION, VOLUME_SURGE_BREAKOUT, WHALE_MOMENTUM will all begin contributing.
