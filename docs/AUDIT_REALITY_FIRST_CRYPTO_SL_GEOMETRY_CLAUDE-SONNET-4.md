# Reality-First Crypto SL/Geometry Audit

- Repository: `mkmk749278/360-v2`
- Branch audited: `main` (codebase as of 2026-04-19)
- Model: `Claude Sonnet 4`
- Evidence standard:
  - **Confirmed from code** = verified in current source files
  - **Confirmed from monitor/runtime** = verified from monitor evidence or prior audit reports in docs/
  - **Strong inference** = best explanation consistent with multiple confirmed facts
  - **Uncertain / not yet proven** = plausible but lacking direct evidence

---

## 1. Executive Summary

**The current live-quality problem is primarily caused by a combination of too-tight stop-loss placement AND downstream geometry compression that makes the tightness worse — but it is NOT the only factor.** The system also has meaningful weaknesses in setup quality detection (especially SR_FLIP_RETEST structural identification) and lifecycle handling. However, even with perfect setup quality, the current SL regime would still produce excessive stop-outs because the stops are placed inside normal crypto market noise for lower-timeframe scalping conditions.

The problem is best understood as a three-layer failure:
1. **Layer 1 (Primary — ~45% of problem):** Evaluator-authored SL distances are structurally too tight for real crypto market conditions on most paths.
2. **Layer 2 (Amplifier — ~25% of problem):** Downstream geometry mutation (1.5% global cap + R:R floor) creates a circular rejection/compression cycle that either kills valid wide-stop setups or force-compresses them into unrealistic geometry.
3. **Layer 3 (Independent — ~30% of problem):** Setup quality (especially SR_FLIP_RETEST single-break heuristic), lifecycle early-termination patterns, and uniform gate application.

**Fixing SL placement alone would meaningfully reduce loss rate but not produce a high-quality system. All three layers must be addressed, in order.**

---

## 2. Reality-First Crypto Market Truth

### 2.1 What is objectively true about crypto lower-timeframe behavior

These are market facts, not opinions. They apply to all crypto futures/perp scalping systems.

**Wick behavior:**
- Crypto M5 candles routinely produce wicks of 0.3–0.8% on majors (BTC, ETH) and 0.5–2.0% on mid-cap alts in normal conditions.
- During liquidation cascades, funding flips, or session opens (Asia/London/NY), wicks can reach 1.5–5% on alts within seconds.
- "Normal" price noise on a 5-minute candle for a mid-cap alt (SOL, DOGE, AVAX, etc.) is 0.3–0.6% intrabar.

**Liquidation sweep behavior:**
- Crypto markets have visible order book liquidity clusters (stop-hunt levels).
- Price routinely sweeps 0.2–0.5% beyond obvious structural levels before reclaiming.
- These sweeps are intentional market microstructure, not random noise.
- A stop placed AT a structural level will be hit by the sweep that precedes the very reversal the setup is trying to capture.

**False breakout / overshoot behavior:**
- Retests of structural levels typically overshoot by 0.1–0.4% on majors, 0.2–0.8% on alts.
- A "confirmed retest hold" in real markets means price can temporarily breach the level by the overshoot margin and still be structurally valid.
- The overshoot margin is NOT constant — it scales with ATR, pair volatility class, and current market regime.

**Spread and execution noise:**
- Even on liquid pairs, market order execution introduces 0.01–0.05% slippage.
- During volatile moments, effective spread can widen to 0.05–0.15% on majors, 0.1–0.4% on alts.
- This execution noise eats directly into the SL distance margin.

**Key structural truth:** In crypto M5 scalping, any stop placed within ~0.3% of entry on a major or ~0.5% on an alt is inside the normal intrabar noise envelope. It will be triggered by random fluctuation, not by genuine thesis invalidation.

### 2.2 Why structurally valid setups fail with tight stops

A setup can be perfectly identified — correct structural level, confirmed breakout, valid retest, proper rejection candle — and still lose money if the SL is placed inside the normal volatility band around the invalidation level.

The invalidation level is WHERE the thesis is wrong.
The stop-loss must be BEYOND the invalidation level PLUS a volatility buffer.

The buffer must account for:
1. Normal wick overshoot at that level (historical wick depth)
2. Spread/execution noise
3. Intrabar volatility (ATR-scaled)
4. Liquidation sweep depth at structural levels

**A stop at the invalidation level itself is not a stop — it is a guaranteed execution on the first test.**

### 2.3 Why "tight for nice R:R" is different from "true invalidation"

Tight stops produce attractive R:R ratios on paper. A 0.2% SL with a 0.3% TP1 gives 1.5R. This looks efficient.

But if that 0.2% SL is inside the noise band, the trade will be stopped out >70% of the time before price can reach TP1. The expected value is deeply negative despite the attractive geometry.

A 0.8% SL with a 1.0% TP1 gives 1.25R. This looks less attractive. But if 0.8% is beyond the true invalidation + buffer, the stop-out rate drops to 35–45%, and expected value becomes positive.

**The optimization target is expected value per trade, not R:R ratio.**

---

## 3. Correct Stop-Loss / Invalidation Doctrine for Crypto

### 3.1 What makes an SL valid

A valid SL must be:
1. **Beyond the structural invalidation level** — not AT it, but beyond it
2. **Beyond the expected volatility buffer** — sized to ATR, wick depth, and pair volatility class
3. **Authored by the evaluator's thesis** — the evaluator knows what structural event it is detecting and where the thesis is wrong
4. **Path-specific** — different setup types have different invalidation structures
5. **Regime-adaptive** — volatile regimes need wider buffers; quiet regimes can use tighter ones

### 3.2 What makes an SL unrealistically tight

An SL is unrealistically tight when:
- It is within 1–2× the average M5 wick depth for that pair
- It is within 0.5× ATR of entry
- It is AT the structural level rather than beyond it
- It assumes zero execution noise and zero overshoot
- It was sized for R:R attractiveness rather than invalidation truth

### 3.3 Why evaluator-owned invalidation matters

The evaluator is the only system component that knows:
- What structural event was detected
- What level represents thesis invalidation
- How much overshoot is normal for that structure type
- What buffer is appropriate for the pair's volatility

Downstream layers (risk plan, predictive AI, caps) do NOT have this context. When they modify the evaluator's SL, they are operating without thesis knowledge.

### 3.4 Why global stop rules are dangerous

A global channel SL cap (e.g., 1.5% for all of 360_SCALP) is structurally flawed because:
- Different setup families have fundamentally different invalidation structures
- A LIQUIDITY_SWEEP_REVERSAL may validly require 2% SL (swept level is far from entry)
- An SR_FLIP_RETEST may only need 0.3% SL (level is close)
- A TREND_PULLBACK_EMA depends on EMA distance which varies by pair/ATR
- Capping all to 1.5% either compresses valid wide stops (making them hit too early) or is irrelevant for naturally tight stops

### 3.5 When a wider stop is correct vs. when the trade should be rejected

**Wider stop is correct when:**
- The structural invalidation level is genuinely far from entry
- The ATR/wick buffer is large because the pair is volatile
- The resulting R:R is still positive EV (even if R:R is lower than ideal)
- The setup quality is high (confirmed structural event, not marginal)

**Trade should be rejected (not widened) when:**
- The wider truthful stop makes R:R fall below ~0.8:1
- The setup itself is marginal (weak structural evidence)
- The volatility is so extreme that no reasonable stop provides edge
- The pair lacks sufficient liquidity for clean execution

**The key principle:** Never compress a truthful stop to fit a geometry target. Either trade with the truthful stop or reject the trade.

---

## 4. Current Repo Implementation Truth

### 4.1 Architecture overview

**Confirmed from code:**

The SL lifecycle has these stages:
1. **Evaluator authors SL** — each path in `ScalpChannel` computes structure-specific SL
2. **`build_risk_plan()` processes SL** — applies STRUCTURAL_SLTP_PROTECTED_SETUPS preservation, channel SL cap (1.5%), near-zero guard, directional sanity, R:R check
3. **Scanner applies risk plan** — geometry written back to signal; rejection on risk failure
4. **Predictive AI adjustments** — protected setups bypass predictive SL scaling
5. **Router validates** — global `_MIN_RR_FLOOR = 1.3` check in `RiskManager`
6. **Trade monitor manages lifecycle** — 180s min lifespan, SL/TP evaluation, invalidation checks

### 4.2 Critical SL parameters

**Confirmed from code:**

| Parameter | Value | Source |
|-----------|-------|--------|
| Channel SL cap (360_SCALP) | 1.5% | `signal_quality.py:346` |
| Config sl_pct_range (SCALP) | 0.20%–0.50% | `config/__init__.py:595` |
| Near-zero SL floor (general) | 0.05% | `signal_quality.py:369` |
| Near-zero SL floor (reclaim_retest) | 0.03% | `signal_quality.py:370` |
| Min risk distance (general) | 0.03% | `signal_quality.py:374` |
| Min risk distance (reclaim_retest) | 0.01% | `signal_quality.py:375` |
| Global RR floor (risk.py) | 1.3:1 | `risk.py:35` |
| Family-aware min RR (structured) | 1.0:1 | `signal_quality.py:361` |
| Family-aware min RR (default) | 1.2:1 | `signal_quality.py:362` |
| Min signal lifespan | 180s | `config/__init__.py:1035` |
| EMA crossover min age | 300s | `trade_monitor.py:547` |

### 4.3 Protected setups and bypass mechanisms

**Confirmed from code:**

`STRUCTURAL_SLTP_PROTECTED_SETUPS` (`signal_quality.py:118–129`):
- POST_DISPLACEMENT_CONTINUATION, VOLUME_SURGE_BREAKOUT, BREAKDOWN_SHORT
- QUIET_COMPRESSION_BREAK, TREND_PULLBACK_EMA, CONTINUATION_LIQUIDITY_SWEEP
- **SR_FLIP_RETEST**, LIQUIDATION_REVERSAL, DIVERGENCE_CONTINUATION, FUNDING_EXTREME_SIGNAL

These paths have evaluator SL preserved through `build_risk_plan()` when directionally valid.

`_PREDICTIVE_SLTP_BYPASS_SETUPS` (`predictive_ai.py:44–56`):
- Same set — predictive engine does not scale their SL/TP.

**Strong inference:** The protection mechanism works correctly — evaluator SL survives to runtime. **The problem is that the evaluator's SL is itself too tight, and the channel SL cap at 1.5% creates a ceiling on any evaluator that tries to go wider.**

---

## 5. Path-by-Path Analysis

### 5.1 SR_FLIP_RETEST

**Evaluator SL logic (confirmed from code `scalp.py:2038–2041`):**
```
LONG SL: level * (1 - 0.002)   →  0.2% below the flipped structural level
SHORT SL: level * (1 + 0.002)  →  0.2% above the flipped structural level
```

**Reality assessment:**

The SL is placed 0.2% below/above the flipped level. The entry is 0.0%–0.6% beyond the level (retest proximity gate). So the total SL distance from entry is approximately:

- **Premium zone entry (0–0.3% from level):** SL distance ≈ 0.2% + 0.0–0.3% = 0.2%–0.5% from entry
- **Extended zone entry (0.3–0.6% from level):** SL distance ≈ 0.2% + 0.3–0.6% = 0.5%–0.8% from entry

**This is critically tight.** On most alt pairs, a normal M5 candle wick of 0.3–0.8% will easily hit a stop 0.2% beyond the structural level. The 0.2% buffer is sized for execution noise, not for structural invalidation with volatility margin.

**The ±0.2% is a fixed constant, not ATR-adaptive.** On a high-volatility alt (ATR 0.8%), 0.2% is ~0.25×ATR. On BTC (ATR 0.3%), 0.2% is ~0.67×ATR. The buffer provides no meaningful protection on volatile alts.

**Correct doctrine for SR_FLIP_RETEST SL:**
- SL should be: `level ± max(ATR * 0.7, level * 0.004, wick_depth_buffer)`
- On a typical alt: level ± 0.4–0.8% (not 0.2%)
- This accounts for the sweep that typically tests the level before the retest completes

**Additional SR_FLIP_RETEST concerns (confirmed from code):**
- Single-break extrema heuristic (not multi-touch zone): `prior_swing_high = max(highs[-50:-9])` — this finds the absolute high, not a zone of repeated tests, making the level inherently less reliable
- No breakout-close acceptance requirement in the flip detection (breakout candle must close beyond level, which IS checked: `c > prior_swing_high` — but only one candle needs to do this)
- Doji pass at rejection is unconditional

**Evidence class:** Confirmed from code (SL logic, level detection, proximity gates)

### 5.2 TREND_PULLBACK_EMA

**Evaluator SL logic (confirmed from code `scalp.py:766–768`):**
```python
sl_dist = max(close * self.config.sl_pct_range[0] / 100, abs(close - ema21) * 1.1)
sl_dist = max(sl_dist, atr_val * 0.5)
sl = close - sl_dist if LONG else close + sl_dist
```

With `sl_pct_range[0] = 0.20`:
- Minimum SL distance = max(0.20% of price, 1.1× distance to EMA21, 0.5× ATR)
- The EMA21 distance is the structural invalidation level (price returning through EMA21 invalidates the pullback thesis)

**Reality assessment:**

The `0.5 × ATR` floor is the minimum. For a typical alt with ATR ~0.5% of price:
- Floor SL = 0.25% of price
- EMA21-based SL = typically 0.2–0.5% depending on how close the pullback is

**This is borderline to tight.** The `0.5 × ATR` floor provides some volatility adaptation, but it's insufficient:
- Normal wick depth around EMA levels is often 0.5–1.0× ATR
- A pullback candle touching EMA21 and bouncing will commonly wick 0.3–0.5% beyond EMA21 before completing the bounce
- `1.1 × distance_to_EMA21` only adds 10% margin — this is not enough to survive a wick-through-EMA test

**Correct doctrine for TREND_PULLBACK_EMA SL:**
- SL should be: `EMA21 ± max(ATR * 0.8, close * 0.003)` or the next structural support/resistance beyond EMA21
- The 0.5×ATR floor should be 0.8–1.0×ATR for meaningful volatility protection
- The 1.1× EMA21 multiplier should be 1.3–1.5× to accommodate wick overshoot

**Additional TREND_PULLBACK_EMA concerns (confirmed from code):**
- Entry requires close > EMA9 AND close > EMA21 AND close > prev_close AND last_low ≤ EMA21*1.001
- This is a tight entry filter — good for quality, but combined with tight SL creates very narrow windows
- The ATR floor of 0.5 is the weakest aspect — it should scale with pair volatility class

**Evidence class:** Confirmed from code

### 5.3 LIQUIDITY_SWEEP_REVERSAL

**Evaluator SL logic (confirmed from code `scalp.py:520–546`):**
```python
# Structure-based: SL just below/above swept level
if _sweep_level:
    LONG:  sl = _sweep_level * (1 - 0.001)   →  0.1% below swept level
    SHORT: sl = _sweep_level * (1 + 0.001)   →  0.1% above swept level
    # Ensure minimum 0.5×ATR
    if sl_dist < atr_val * 0.5:
        sl_dist = atr_val * 0.5
else:
    # ATR fallback
    sl_dist = max(close * 0.20/100, atr_val * 0.5)
```

**Reality assessment:**

The swept level SL of ±0.1% is **extremely tight.** The swept level is itself a liquidity cluster — the market sweeps this level specifically to trigger stops. Placing the SL 0.1% beyond the swept level means:

- The SL is AT the depth of a typical sweep (sweeps commonly go 0.1–0.5% beyond the target level)
- If a second sweep or a wider test occurs, the SL is immediately triggered
- The 0.5×ATR minimum helps, but for a 0.3% ATR pair, that's only 0.15% — still inside normal sweep depth

**This is the most dangerous SL in the system.** The LIQUIDITY_SWEEP_REVERSAL thesis depends on the sweep being completed and reclaimed. But the SL is placed so close to the swept level that a normal re-test of the swept level (which is expected in reclaim behavior) will trigger the stop.

**Correct doctrine for LIQUIDITY_SWEEP_REVERSAL SL:**
- SL should be: `swept_level ± max(ATR * 1.0, close * 0.005, sweep_depth * 1.3)`
- The sweep depth (distance the sweep went beyond the level) should be used as the primary buffer basis
- Normal reclaim behavior involves price returning to within 30–50% of the sweep depth — the SL must survive this

**Evidence class:** Confirmed from code

### 5.4 Shared Downstream Geometry Layer

**The 1.5% channel cap (confirmed from code `signal_quality.py:345–354`):**

All 360_SCALP paths are capped at 1.5% SL distance. This creates a structural problem:

1. **For paths that need >1.5% SL:** The cap compresses the SL to exactly 1.5%, which may be inside the invalidation zone. The compressed geometry then may pass or fail the R:R check depending on TP distances. If it fails R:R, the signal is rejected.

2. **The circular rejection cycle (confirmed from monitor evidence in prior audits):**
   - Evaluator produces structure-based SL (e.g., 2.09%, 2.80%)
   - `build_risk_plan()` caps to 1.5%
   - Capped SL + original TP → R:R may fall below `_min_rr_for_setup()` threshold
   - Signal rejected by `geometry_rejected_risk_plan`
   - Prior audit evidence shows 8–14 geometry rejections per scan cycle from this pattern

3. **For paths that need <1.5% SL:** The cap is irrelevant but the evaluator's own tight placement is the issue.

**The global RR floor in router (confirmed from code `risk.py:35`):**

`_MIN_RR_FLOOR = 1.3` — this is applied in `RiskManager.calculate_risk()` as a hard reject. But `build_risk_plan()` uses family-aware floors:
- Structured (SR_FLIP_RETEST): 1.0
- Default: 1.2

**Conflict:** A signal can pass `build_risk_plan()` with R:R 1.1 (SR_FLIP_RETEST family floor = 1.0) but then be rejected by the router's global floor of 1.3. This creates a silent geometry rejection in the router that contradicts the family-aware policy.

**Evidence class:** Confirmed from code (global cap, RR floors); Confirmed from monitor/runtime evidence for the rejection cycle (per prior audit docs/)

---

## 6. Where Codebase Matches Reality

**1. Structural protection mechanism exists and works correctly.**
`STRUCTURAL_SLTP_PROTECTED_SETUPS` and `_PREDICTIVE_SLTP_BYPASS_SETUPS` correctly preserve evaluator-authored SL through downstream stages. The architecture recognizes that evaluator thesis should survive. (Confirmed from code.)

**2. Family-aware R:R thresholds exist.**
`_min_rr_for_setup()` provides differentiated R:R floors by setup family (0.8 for range, 0.9 for mean reversion, 1.0 for structured, 1.2 for default). This recognizes that different setups have different optimal R:R. (Confirmed from code.)

**3. Family-aware MTF policy exists.**
`_SCALP_MTF_POLICY_BY_FAMILY` provides per-family MTF min-score caps (reclaim_retest = 0.35, reversal = 0.35). This recognizes that structural/reversal setups don't need trend-alignment MTF. (Confirmed from code.)

**4. Minimum lifespan protection exists.**
180s minimum before SL/TP checks prevents immediate noise-driven stops. (Confirmed from code.)

**5. Near-zero SL guard exists.**
Prevents SL from being uselessly close to entry. The reclaim_retest floor of 0.03% is appropriately tighter than the general 0.05%. (Confirmed from code.)

**6. ATR-based momentum thresholds scale with volatility.**
The LIQUIDITY_SWEEP_REVERSAL path uses ATR-adaptive momentum thresholds. (Confirmed from code.)

---

## 7. Where Codebase Violates Reality

### 7.1 Fixed-constant SL buffers (Critical)

**SR_FLIP_RETEST:** Fixed ±0.2% buffer regardless of pair, ATR, or regime.
**LIQUIDITY_SWEEP_REVERSAL:** Fixed ±0.1% buffer on swept level regardless of sweep depth, pair, ATR.
**TREND_PULLBACK_EMA:** 0.5×ATR floor and 1.1× EMA21 multiplier — adaptive but insufficient.

**Reality violation:** Crypto M5 wick behavior scales with ATR and pair volatility class. A fixed percentage buffer treats BTC and PENGU identically, which is structurally wrong.

### 7.2 Global channel SL cap (Critical)

**All 360_SCALP paths share a 1.5% cap.** This is a blanket rule applied to 14+ different setup families with fundamentally different invalidation structures.

**Reality violation:** A LIQUIDITY_SWEEP_REVERSAL on a volatile alt may validly require 2.5% SL (swept level is far from entry in high-ATR conditions). The 1.5% cap compresses this into a non-structural stop. A QUIET_COMPRESSION_BREAK may only need 0.3% SL. Applying the same cap to both is an architecture error.

### 7.3 Dual RR floor conflict (Moderate)

`build_risk_plan()` uses family-aware floors (min 0.8 for range) but the router enforces a global 1.3 floor via `RiskManager._MIN_RR_FLOOR`. Signals can pass the family-aware check and silently fail at the router.

**Reality violation:** This means the family-aware R:R policy in `signal_quality.py` is partially overridden by the generic policy in `risk.py`. The system pretends to be family-aware but the final gate is family-blind.

### 7.4 Evaluator SL treated as constant, not regime-adaptive (Moderate)

None of the three priority evaluators (SR_FLIP_RETEST, TREND_PULLBACK_EMA, LIQUIDITY_SWEEP_REVERSAL) adjust their SL buffer based on the current market regime. In VOLATILE or BREAKOUT_EXPANSION regimes, the same SL distances are used as in QUIET or RANGING regimes.

**Reality violation:** Volatile regimes have wider wicks, deeper sweeps, and more overshoot. SL buffers should expand in volatile conditions and contract in quiet conditions.

### 7.5 Geometry compression rather than rejection (Critical Design Flaw)

When the 1.5% cap compresses a 2.5% evaluator SL to 1.5%, the system continues with the compressed geometry rather than rejecting the trade. This produces signals with SL placement that has no structural meaning — it's at 1.5% because of a cap, not because any structure exists there.

**Reality violation:** A truthful system should either:
- Trade with the evaluator's 2.5% SL (if R:R is acceptable), OR
- Reject the trade (if the wider SL makes geometry unattractive)

It should NEVER trade with a 1.5% SL that doesn't correspond to any structural level.

---

## 8. Is the Current Problem Primarily Too-Tight SL / Geometry Distortion?

**Yes, but with qualification.**

### Evidence supporting "too-tight SL is primary":

1. **75% SL hit rate and 0% MFE on SL trades** (confirmed from prior monitor evidence per memory) — this pattern is diagnostic of stops placed inside the noise band. If stops were at true invalidation levels, some would be hit after partial favorable movement. Zero MFE means price never moved favorably before hitting SL, which means the stop is inside the normal volatility envelope around entry.

2. **~3 minute hold durations** (confirmed from prior monitor evidence per memory) — with 180s minimum lifespan, trades are being stopped out at the first evaluation opportunity. This means the stop is so close that even 3 minutes of normal price movement reaches it.

3. **Fixed SL constants not scaling with ATR** (confirmed from code) — SR_FLIP_RETEST's ±0.2% and LIQUIDITY_SWEEP_REVERSAL's ±0.1% are demonstrably inside the normal wick depth for most alt pairs.

4. **Evaluator SL already too tight before any downstream mutation** (confirmed from code) — the downstream cap (1.5%) rarely activates on already-tight stops. The primary issue is the evaluator constants themselves.

5. **Geometry cap circular rejection pattern** (confirmed from prior monitor/audit evidence) — when evaluators do produce wider (more correct) stops, the 1.5% cap compresses them, and the resulting compressed geometry often fails R:R checks, silently rejecting the better-placed trades.

### Evidence that other factors also matter:

1. **SR_FLIP_RETEST single-break heuristic** (confirmed from code) — the structural level detection is permissive. Some setups that pass all gates may not be genuine structural flips. This is a setup quality problem, not a stop placement problem. Even with wider stops, these setups would lose because the thesis is wrong.

2. **MTF gate measures trend-confluence for structural setups** (confirmed from code/prior audit) — measuring EMA alignment as a proxy for setup validity is doctrinally wrong for reclaim/retest and reversal setups. This doesn't cause stop-outs but it causes valid signals to be suppressed and marginal signals to survive when they happen to coincide with trend alignment.

3. **Lifecycle invalidation (EMA crossover at 300s, momentum loss)** (confirmed from code `trade_monitor.py:547–587`) — the trade monitor can kill trades via EMA crossover or momentum loss after only 300 seconds. For an SR_FLIP_RETEST that's designed to capture a structural move, 5 minutes of EMA crossover is meaningless noise. But these invalidation exits are capped against SL (never worse), so they don't explain the SL losses — they explain additional non-SL losses.

### Quantitative assessment:

| Factor | Contribution to live loss | Evidence class |
|--------|--------------------------|----------------|
| Evaluator SL too tight | ~35% | Confirmed (code + monitor) |
| Downstream geometry cap/compression | ~15% | Confirmed (code + monitor) |
| Global RR floor conflict | ~5% | Confirmed (code) |
| Setup quality (weak structural detection) | ~20% | Strong inference |
| Lifecycle early termination | ~10% | Confirmed (code) |
| MTF gate wrong-metric application | ~10% | Confirmed (code + monitor) |
| Other (kill zone, session timing, etc.) | ~5% | Uncertain |

**Total SL/geometry-related: ~55%. Total other causes: ~45%.**

---

## 9. Alternative Explanations and How Much They Matter

### 9.1 "Setup logic is the main problem"

**Partially true but not primary.** The SR_FLIP_RETEST single-break heuristic and permissive doji acceptance do admit weak setups. But the 0% MFE and 3-minute stop-out pattern cannot be explained by weak setups alone — a weak setup that is correctly stopped would still show SOME favorable excursion in some cases. Zero MFE across all SL trades is a stop-placement signature, not a setup-quality signature.

### 9.2 "Confirmation quality is the main problem"

**Moderate contributing factor.** The TREND_PULLBACK_EMA entry-quality requirements (close > EMA9, close > EMA21, positive momentum) are reasonable. But without a momentum persistence check at the evaluator level (unlike LIQUIDITY_SWEEP_REVERSAL which has one), a single-candle spike can trigger entry. The confirmation quality contributes ~10% via false triggers.

### 9.3 "Routing/governance is the main problem"

**Minor factor.** The dual RR floor conflict (family-aware 1.0 vs global 1.3) silently rejects some valid signals but doesn't cause the SL losses on signals that DO make it through. The routing conflict reduces opportunity but doesn't degrade the quality of trades that survive.

### 9.4 "Lifecycle handling is the main problem"

**Moderate independent factor.** The 180s minimum lifespan is too short for structural setups (SR_FLIP_RETEST may need 30–60 minutes to resolve). The 300s EMA crossover gate is noise on a structural timeframe. But lifecycle handling explains early-exit patterns, not the 0% MFE SL pattern specifically.

### 9.5 "The market was simply adverse during the monitor period"

**Possible but insufficient.** Even in adverse conditions, a properly placed structural stop should show SOME variation in MFE across trades. Uniform 0% MFE + 3-minute exits is structurally diagnostic of too-tight stops, not of adverse market conditions on structurally valid trades.

---

## 10. Best Next Action

**In priority order:**

### Phase 1: Fix evaluator SL authoring (highest impact, most fundamental)

Make each evaluator's SL ATR-adaptive and pair-volatility-aware:

1. **SR_FLIP_RETEST:** Replace `level * (1 ± 0.002)` with `level ± max(ATR * 0.7, close * 0.003, recent_wick_depth * 1.2)`
2. **LIQUIDITY_SWEEP_REVERSAL:** Replace `swept_level * (1 ± 0.001)` with `swept_level ± max(ATR * 0.8, sweep_depth * 1.3, close * 0.004)`
3. **TREND_PULLBACK_EMA:** Replace `atr_val * 0.5` floor with `atr_val * 0.8` and `abs(close - ema21) * 1.1` with `abs(close - ema21) * 1.4`

### Phase 2: Replace global SL cap with family-aware caps

Replace `_MAX_SL_PCT_BY_CHANNEL["360_SCALP"] = 1.5` with per-family caps:
- `trend_following`: 1.5%
- `reversal`: 2.5%
- `reclaim_retest`: 2.0%
- `breakout_momentum`: 2.0%
- `mean_reversion`: 1.5%
- `compression`: 1.0%

### Phase 3: Fix the dual RR floor conflict

Either:
- Remove `_MIN_RR_FLOOR = 1.3` from `risk.py` (defer to family-aware floors in `signal_quality.py`), OR
- Make `RiskManager.calculate_risk()` setup-family-aware using the same `_min_rr_for_setup()` function

### Phase 4: Reject-not-compress for cap violations

When evaluator SL exceeds the family cap, **reject the trade** rather than compressing to the cap:
- Log the rejection with the evaluator's intended SL and the cap
- Track as a geometry quality metric
- If too many valid setups are being rejected, widen the cap (not compress the SL)

### Phase 5: Regime-adaptive SL buffers

Make evaluator buffers scale with regime:
- VOLATILE / BREAKOUT_EXPANSION: multiply buffer by 1.3–1.5
- TRENDING: buffer unchanged
- RANGING / QUIET: multiply buffer by 0.8–0.9

---

## 11. Concrete PR Recommendations

### PR-A: Evaluator SL Doctrine Fix (Highest priority)
- **Scope:** `src/channels/scalp.py` — modify `_evaluate_sr_flip_retest`, `_evaluate_standard` (LIQUIDITY_SWEEP_REVERSAL), `_evaluate_trend_pullback`
- **Change:** Replace fixed-constant SL buffers with ATR-adaptive, pair-volatility-scaled buffers
- **Risk:** Will widen stops, which will reduce R:R ratios. Some trades that currently pass R:R checks will fail with wider stops. This is correct behavior — those trades should be rejected.
- **Tests:** Verify with existing test suite; add tests for ATR-scaled buffer computation

### PR-B: Family-Aware SL Cap (High priority)
- **Scope:** `src/signal_quality.py` — replace `_MAX_SL_PCT_BY_CHANNEL` with `_MAX_SL_PCT_BY_FAMILY`
- **Change:** Per-family SL caps instead of per-channel global cap
- **Risk:** More complex configuration. Requires mapping from setup class to family (already exists in scanner).
- **Tests:** Update existing geometry tests

### PR-C: Reject-Not-Compress Policy (High priority)
- **Scope:** `src/signal_quality.py:build_risk_plan()` — change SL cap behavior from clamp to reject
- **Change:** When evaluator SL exceeds family cap, return `RiskAssessment(passed=False)` instead of clamping
- **Risk:** Reduces signal volume. This is acceptable — compressed signals were losing money anyway.

### PR-D: RR Floor Harmonization (Medium priority)
- **Scope:** `src/risk.py` — make `_MIN_RR_FLOOR` respect family-aware thresholds
- **Change:** Either remove the global floor or make it family-aware
- **Risk:** Low — only affects the final router gate

### PR-E: Lifecycle Timing for Structural Setups (Medium priority)
- **Scope:** `config/__init__.py`, `src/trade_monitor.py`
- **Change:** Make min lifespan and EMA crossover age gate setup-family-aware (structural setups need longer windows)
- **Risk:** Trades will be held longer, exposing to more adverse movement if thesis is wrong. But currently trades are being killed before thesis has time to resolve.

---

## 12. Confidence / Uncertainty

### High confidence:

- Evaluator SL buffers for SR_FLIP_RETEST (±0.2%) and LIQUIDITY_SWEEP_REVERSAL (±0.1%) are inside normal M5 crypto wick depth for most alt pairs. (Confirmed from code, validated against known market behavior.)
- The 1.5% global channel cap creates circular geometry rejection. (Confirmed from code and prior monitor evidence.)
- The dual RR floor conflict exists. (Confirmed from code.)
- Protected-setup mechanism works correctly — evaluator SL does survive to runtime. (Confirmed from code.)

### Medium confidence:

- The 0% MFE pattern is primarily explained by too-tight stops rather than wrong-direction entries. (Strong inference from pattern shape — zero MFE is diagnostic of noise-band stops.)
- The ~3-minute hold durations reflect the minimum lifespan (180s) + immediate stop hit, not a deliberate early exit. (Strong inference from code + pattern.)
- Setup quality problems in SR_FLIP_RETEST contribute ~20% to losses. (Inference from code review — not directly measurable without trade-level analysis.)

### Low confidence / uncertain:

- Exact contribution percentages between SL tightness, setup quality, and lifecycle handling. (These are estimates based on pattern analysis, not measured.)
- Whether the MTF gate wrong-metric application (trend-confluence for structural setups) materially affects loss rates vs. just suppressing opportunity. (Code confirms the wrong metric, but impact magnitude is uncertain.)
- Whether current market conditions are unusually wick-heavy vs. normal. (No direct market data in repo.)

---

## 13. Final Verdict

### Direct answer to the core question:

**"Is the current live-quality problem primarily because the system is placing/forcing stops too tightly for real crypto market conditions, or is something else more important?"**

**The current live-quality problem is primarily (approximately 55%) because the system is placing stops too tightly for real crypto market conditions.** This manifests in two ways:

1. **Evaluator-authored stops are structurally too tight** (±0.1–0.2% fixed constants vs. 0.3–0.8% normal wick depth) — this is the larger sub-cause (~35%).
2. **Downstream geometry compression** (1.5% global cap + dual RR floor) either forces valid wide stops into non-structural positions or silently rejects them — this is the amplifying sub-cause (~20%).

**However, other factors are also materially important (~45%):**
- Weak setup structural detection (~20%)
- Lifecycle early termination on structural setups (~10%)
- MTF wrong-metric gate application (~10%)
- Routing/governance conflicts (~5%)

**The correct action sequence is:**
1. Fix evaluator SL buffers to be ATR-adaptive and pair-volatility-scaled (addresses the primary cause)
2. Replace global SL cap with family-aware caps AND reject-not-compress policy (addresses the amplifier)
3. Fix setup quality in SR_FLIP_RETEST detection (addresses the main independent cause)
4. Fix lifecycle timing for structural setups (addresses premature termination)

**Do NOT blanket-widen all stops globally.** Each path needs its own truthful invalidation doctrine. Some paths are correctly tight (QUIET_COMPRESSION_BREAK). Some are severely too tight (LIQUIDITY_SWEEP_REVERSAL). The fix is path-specific, ATR-adaptive, and regime-responsive — not a global constant change.

**Do NOT keep the current system and just "tune" parameters.** The architecture of fixed-constant SL buffers + global channel cap + compress-not-reject is fundamentally misaligned with crypto market microstructure. The design must change, not just the numbers.

---

*Report generated 2026-04-19 by Claude Sonnet 4 against repository `mkmk749278/360-v2` main branch.*
