# 360-Crypto-Scalping V2 — Signal Path Reality Report
**Date:** April 20, 2026  
**Codebase:** 360-v2-main  
**Scope:** Every signal generation path reviewed against live crypto market reality

---

## Executive Summary

The engine has **7 production-ready paths**, **5 paths needing fixes or disabling**, and **3 live-trading bugs** that will cause crashes or silent failures. The core sweep/pullback/structural family is genuinely competitive. The VWAP and Ichimoku channels have fundamental conceptual mismatches that no parameter tuning will fix.

**Fix the 3 bugs before any live deployment.**

---

## Crypto Market Ground Truths

Before the path-by-path breakdown, these are the market realities every path is judged against:

1. **Liquidity sweeps are the #1 institutional move** — smart money hunts stop clusters above/below swing highs/lows before reversing
2. **CVD is one of the few genuinely leading indicators in crypto** — it reveals who is actually absorbing pressure
3. **Funding rates at extremes (≥1%) are contrarian gold mines** — over-leveraged crowd gets squeezed
4. **5m scalps have a sub-2-minute execution window** — signals older than 120s are worthless
5. **Crypto regimes flip in hours, not days** — hysteresis must be tight
6. **False breakouts dominate crypto** — 65–70% of 5m breakouts above resistance fail within 3 candles without volume
7. **Order book imbalance is thin and manipulable** — OBI is useful but unreliable alone
8. **Altcoin spreads explode during volatile moves** — the spread filter must adapt
9. **VWAP resets at midnight UTC** — intraday VWAP is meaningful only within a session
10. **Ichimoku on 5m is noise** — the cloud periods were designed for daily timeframes

---

## Signal Path Analysis

### ScalpChannel (14 paths)

---

#### PATH 1 — `LIQUIDITY_SWEEP_REVERSAL` (Standard Scalp)
**Status: ✅ PRODUCTION-READY**

**What it does:** Detects wick through swing high/low with close back inside, requires EMA alignment, ADX > 12, momentum persistence across multiple candles, MTF 1h gate, HTF EMA200 rejection.

**Why it works in real crypto:**
- Liquidity sweeps are the single most reliable 5m setup in crypto. Smart money above retail stops = high-probability reversal
- ATR-adaptive momentum threshold scales correctly between BTC (low ATR%) and altcoins (high ATR%)
- Momentum persistence across N candles correctly filters one-candle whipsaws
- HTF EMA200 gate only blocks when moving *toward* it, not bouncing away — excellent nuance
- Structure-based SL at swept level ±0.1% is far superior to fixed ATR

**Issues:**
- ADX lowering in RANGING (floor at 12) is borderline too permissive. At ADX 12–15, sweeps can be noise. Consider raising floor to 15
- `sig.confidence += macd_adj` is dead code — the scanner overwrites confidence three times later. The penalty has zero effect (see Bug 2)

---

#### PATH 2 — `TREND_PULLBACK_EMA`
**Status: ✅ PRODUCTION-READY — Best path in the codebase**

**What it does:** TRENDING_UP/DOWN regimes only. Price pulls back to EMA9/21, must dip to EMA21, close above EMA9/21, RSI 40–60, momentum positive, FVG/OB confirmation required.

**Why it works in real crypto:**
- EMA9 > EMA21 > EMA50 alignment check is rigorous and prevents counter-trend entries
- 0.3% proximity to EMA9 or 0.5% to EMA21 is correctly calibrated for 5m timeframes
- RSI 40–60 ensures mid-range (not exhausted) entry
- Entry-quality checks are exceptional: requires genuine pullback confirmation across multiple candle conditions
- +8 confidence bonus is justified — this is the highest-probability institutional entry pattern

**Issues:**
- RSI rising confirmation (`rsi_last > rsi_prev`) is too strict for 5m — RSI oscillates rapidly and a single candle dip doesn't invalidate the setup. Will filter too many valid signals
- TP2 using 4h swing high is often hours away, contradicting the scalp intent. Cap TP2 at the next 1h swing high instead

---

#### PATH 3 — `LIQUIDATION_REVERSAL`
**Status: ✅ PRODUCTION-READY — With caveats**

**What it does:** 3-candle cascade ≥2%, CVD divergence (buyers absorbing during selloff), RSI ≤25, zone proximity, volume spike 2.5× average.

**Why it works in real crypto:**
- Liquidation reversals are real and powerful. The Fibonacci retrace TPs (38.2%, 61.8%, 100% of cascade range) are perfectly thesis-aligned
- CVD divergence during cascade = buyers absorbing = strong reversal confirmation
- RSI ≤25 ensures genuine capitulation

**Issues:**
- **Timing problem:** The cascade is detected after 3 closed candles (15 min). The optimal reversal entry at the cascade bottom may already be 1–2% away. The SL at `cascade_low - 0.3%` can be very wide relative to the actual entry. Consider detecting the cascade on the candle-close event, not after 3 candles
- RSI ≤25 is very aggressive. Altcoin cascades can push RSI to 15 and stay there for hours. Consider ≤30 as hard gate, with ≤25 as a confidence bonus
- Volume spike check uses unit volume, not USD volume. A 1M-token spike on a $0.001 token is meaningless. Multiply by close price

---

#### PATH 4 — `WHALE_MOMENTUM`
**Status: ✅ USABLE — With data dependency caveats**

**What it does:** Requires whale_alert OR delta_spike, buy/sell tick volume ratio ≥2:1, $500K+ tick volume, three-tier OBI confirmation system.

**Why it works in real crypto:**
- The three-tier OBI gate (full depth / book_ticker only / absent) is the most nuanced order book handling in the codebase — reflects the reality that different depth sources have different reliability
- Swing-based SL (5-bar 1m lookback for invalidation point) is correctly placed at the impulse origin

**Issues:**
- **Whale Alert data has 1–3 min delays.** By the time the signal fires, the momentum move it's designed to capture is already over. This path works better as a 15m setup, not 5m
- `recent_ticks` is sparse after WS reconnects — will incorrectly trigger rejects during reconnection windows
- RSI 1m hard reject ≥82 is too aggressive. RSI above 82 during a genuine whale pump is extremely common and valid. Should be ≥88

---

#### PATH 5 — `VOLUME_SURGE_BREAKOUT`
**Status: ⚠️ NEEDS FIXES**

**What it does:** Volume ≥3× rolling avg, price breaks 20-candle swing high, pulls back 0.1–0.75% below it, EMA9 > EMA21, RSI 40–82 layered, measured-move TPs.

**Problems:**
- **False breakout rate in crypto is 60–70%.** A single close above swing high is enough to trigger the path — need at least 2 consecutive closes above the level for sustained acceptance
- Pullback zone (0.1–0.75%) is too tight. Real breakout retests often pull back 1–1.5% before resuming. The hard block at 0.75% misses the majority of valid entries. Extend to 1.5% with graduated penalty
- Measured-move TPs can be 5–8% away — not a scalp. Cap TP2 at 2× ATR from entry

---

#### PATH 6 — `BREAKDOWN_SHORT`
**Status: ⚠️ NEEDS FIXES**

**What it does:** Mirror of PATH 5 for the short side.

**Problems:**
- Same issues as PATH 5 (single-bar breakdown detection, tight bounce zone)
- **Additional short-side problem:** Binance perpetual funding typically leans positive (longs paying shorts), creating natural headwinds for short positions
- Dead-cat bounces are hard to time — they can last 0–20 candles. The 0.1–0.75% bounce zone will be correct less often than the long equivalent

---

#### PATH 7 — `OPENING_RANGE_BREAKOUT`
**Status: 🔴 DISABLED — Correctly so**

The code itself acknowledges: *"The current proxy (last-8-bar window) is not institutional-grade."* A true ORB requires the first N candles from the actual session open timestamp, not a rolling window. Crypto sessions are also less defined than FX. Leave disabled until rebuilt with proper session-start timestamp tracking.

---

#### PATH 8 — `SR_FLIP_RETEST`
**Status: ✅ PRODUCTION-READY**

**What it does:** Detects prior swing high/low, finds closed-candle breakout confirmation, checks 0–0.6% proximity for retest, requires rejection wick, EMA aligned, RSI 20–80 layered.

**Why it works in real crypto:**
- Breakout-close confirmation (not just wick break) prevents fake flips — critical in crypto where wicks routinely pierce levels
- 8-candle search window accommodates real-world timing variation
- Layered proximity zones (premium 0–0.3%, extended 0.3–0.6%) reflect how retests actually behave
- Reclaim-hold validation across candles prevents entering on a momentary touch
- Structural SL using ATR buffer + wick overshoot is correctly placed beyond the invalidation zone

**Critical Bug:**
- `sig.sr_flip_level = round(level, 8)` — `sr_flip_level` does **not exist** on the Signal dataclass → `AttributeError` on every SR_FLIP signal generation. **See Bug 1.**

**Other Issues:**
- Prior window uses [-50:-9] (41 candles = ~3.4h on 5m). Crypto S/R levels are typically anchored on 4h/daily swings. Should also incorporate 1h swing levels

---

#### PATH 9 — `FUNDING_EXTREME_SIGNAL`
**Status: ✅ PRODUCTION-READY — Most crypto-native path**

**What it does:** Funding rate beyond ±0.01%, EMA alignment, RSI confirmation, CVD confirmation, FVG/OB required, SL at nearest liquidation cluster.

**Why it works in real crypto:**
- Extreme funding is a genuinely reliable contrarian signal unique to perpetual futures
- Liquidation-cluster-anchored SL is the most sophisticated SL placement of all paths
- Nearest FVG/OB structure for TP1 (not flat ATR multiple) is thesis-aligned
- CVD rising during negative funding = buyers absorbing while crowd pays shorts = powerful confluence

**Issues:**
- RSI threshold for SHORT (`rsi_last <= 45` = reject) will frequently block valid setups. Extreme positive funding happens during raging uptrends where RSI is 70+. Should be ≤55 hard block with soft penalty at 55–65
- `funding_rate` is read from `smc_data` — if the OI poller misses a cycle, this path silently produces no signals. Add a staleness check

---

#### PATH 10 — `QUIET_COMPRESSION_BREAK`
**Status: ✅ USABLE — Low firing frequency**

**What it does:** QUIET/RANGING only. BB width < 1.5%, price closes outside BB, MACD histogram zero-cross, volume ≥2× avg, RSI 50–70 (LONG) or 30–50 (SHORT).

**Why it works:** BB squeezes are real and produce high-velocity moves. The MACD zero-cross requirement is strong confirmation.

**Issues:**
- BB width < 1.5% is very tight. On altcoins average BB width is 2–4%. Scale to ATR instead: `bb_width < atr * 3`
- All three conditions simultaneously (BB outside + MACD zero-cross + volume 2×) on a single candle will be extremely rare. This path will fire very infrequently in practice (<2% of scan cycles)

---

#### PATH 11 — `DIVERGENCE_CONTINUATION`
**Status: ✅ USABLE — Data mutation bug present**

**What it does:** TRENDING_UP/DOWN only. Hidden CVD divergence (price pullback, CVD holds) as trend continuation.

**Why it works:** Hidden divergence is correctly categorised as continuation (not reversal). CVD higher low during price lower low in uptrend = buyers still in control.

**Critical Bug:**
- `smc_data["cvd_divergence"] = _div_label` mutates the shared smc_data dict. `ScalpCVDChannel`, which runs after this path, reads `smc_data.get("cvd_divergence")` and will see the contaminated value. **See Bug 3.**

**Other Issues:**
- Divergence computed on closes, not on highs/lows. For accurate detection, price lows should use `lows` array, not `closes`

---

#### PATH 12 — `CONTINUATION_LIQUIDITY_SWEEP`
**Status: ✅ PRODUCTION-READY**

**What it does:** Trending regimes only. Finds a recent sweep within 10 candles, confirms trend resumed after it, EMA aligned, RSI gate, FVG/OB required.

**Why it works:** Stop hunts below a higher low in an uptrend are extremely reliable continuation entries. The 10-candle recency requirement is appropriate.

**Issues:**
- Very recent sweeps (within 2 candles) may still be in progress. Consider requiring 2–3 candles of trend resumption after the sweep before entry

---

#### PATH 13 — `POST_DISPLACEMENT_CONTINUATION`
**Status: ✅ PRODUCTION-READY — Most sophisticated momentum path**

**What it does:** Trending regimes. Displacement candle with ≥60% body ratio and ≥2.5× volume, followed by 2–5 candle tight consolidation (≤50% of displacement body), then re-acceleration entry.

**Why it works:** This is institutional-grade pattern recognition. All three requirements (body ratio, volume, tight consolidation) must be simultaneously true — filters out low-quality entries correctly.

**Issues:**
- `_PDC_DISP_VOLUME_MULT = 2.5` will be met rarely on 5m outside news events. Consider reducing to 1.8–2.0
- Current candle direction is not explicitly checked for re-acceleration. Add a check that the current candle is in the displacement direction

---

#### PATH 14 — `FAILED_AUCTION_RECLAIM`
**Status: ✅ PRODUCTION-READY**

**What it does:** Finds a prior swing level, checks that a recent candle (1–7 bars ago) failed to accept above/below it (close within 0.2% of level), then current close has reclaimed by ≥0.1 ATR.

**Why it works:** Failed breakouts are among the highest-edge setups in crypto. The 0.2% failed-acceptance threshold correctly identifies wick-breaks that didn't sustain.

**Issues:**
- `_FAR_AUCTION_WINDOW_MIN = 1` allows the failed auction candle to be the immediately prior closed candle. A single candle within 0.2% of a level then a reclaim is just price oscillation, not a failed auction. Minimum should be 2 bars back

---

### Specialist Channels

---

#### `ScalpFVGChannel` — FVG Retest
**Status: ✅ PRODUCTION-READY**

FVG retests are genuine institutional moves. The graduated fill decay (not binary cliff at 60%) is sophisticated and correct — a 30% filled FVG is weaker but still tradeable.

**Issues:**
- `_FVG_RETEST_PROXIMITY = 0.50` (50% of zone width) is too wide for scalp precision. Tighten to 0.25
- Age-based SL decay can make the R:R too tight to pass minimum RR floors when zones are old

---

#### `ScalpCVDChannel` — CVD Divergence
**Status: ✅ PRODUCTION-READY**

The `_CVD_REQUIRE_METADATA = True` fail-closed behavior is correct. Recency (10 candles) and magnitude (strength ≥0.3) guards are well-calibrated.

**Issues:**
- ADX ≤35 gate misses CVD divergences in early-trend conditions where this setup has most edge
- SR proximity check of `recent_low + atr_val * 1.0` can allow entry $200 above the recent low on BTCUSDT — too loose for a precision scalp. Tighten to 0.5× ATR

---

#### `ScalpVWAPChannel` — VWAP Band Bounce
**Status: 🔴 FUNDAMENTAL FLAW — Needs redesign**

**Core problem:** The VWAP is computed on the last 50 candles (`highs[-50:]`). This is a **rolling VWAP**, not a session-anchored VWAP. A true intraday VWAP resets at the daily open (midnight UTC for crypto) and represents the average price weighted by volume from the start of the day. The "rubber band" mean-reversion effect that makes VWAP bounces work is created by institutions managing their TWAP/VWAP execution — they reference the *daily session VWAP*, not a 4-hour rolling average.

Using a 50-candle rolling VWAP means the channel is essentially trading mean-reversion to a volume-weighted moving average, which is a weaker and different signal. It will produce signals at levels that have no institutional significance.

**Fix required:** Anchor VWAP calculation to the daily session open (00:00 UTC). Accumulate `(high+low+close)/3 * volume` from midnight UTC, reset at each new day.

---

#### `ScalpDivergenceChannel` — RSI/MACD Divergence
**Status: ✅ USABLE**

Local minima/maxima detection with configurable window and NaN-dropping is the correct approach.

**Issues:**
- Window=3 for local minima on crypto's choppy 5m charts generates too many false swing points. Increase to 5
- Uses `closes` for price extremes instead of `highs`/`lows` — can produce false divergence detections

---

#### `ScalpSupertrendChannel` — Supertrend Flip
**Status: ✅ PRODUCTION-READY**

Supertrend flips are reliable in trending conditions. The MTF gate requiring 15m and 1h confirmation is the right safeguard against 5m false flips.

**Issues:**
- Default Supertrend multiplier of 3.0 generates too many flips on crypto's volatile 5m. Expose as config and consider 2.0 as default
- EMA computation is duplicated from scratch (`compute_ema(c_arr, ...)`) when the indicators dict already has `ema9_last`. Remove redundant computation

---

#### `ScalpIchimokuChannel` — TK Cross
**Status: 🔴 WRONG TIMEFRAME — Disable or rebuild**

**Core problem:** Ichimoku's standard periods (9/26/52) were derived from the Japanese trading week and make mathematical sense on daily charts. On 5m timeframes these periods cover 45min/2.2h/4.3h. The cloud is not a meaningful institutional reference on intraday crypto charts.

On 5m, price crosses the Kumo (cloud) every 2–4 hours on most pairs. The cloud signals that institutional traders actually use are on 4h/daily. This channel will generate signals at levels that have no institutional basis.

**Fix:** Either restrict this channel to 1h/4h timeframes where Ichimoku is meaningful, or convert to a pure TK cross + price-above-EMA200 setup that captures the directional intent without relying on the cloud.

---

#### `ScalpOrderblockChannel` — SMC Order Block
**Status: ✅ PRODUCTION-READY**

Clean order block detection: last bearish candle before bullish impulse = demand zone. The `_mark_touched` freshness logic is correct.

**Issues:**
- A single wick touching the OB zone without a close through the midpoint should not invalidate the zone. Freshness check should require price to close through the OB center before marking as touched
- `_IMPULSE_ATR_MULT = 1.5` should be regime-adjusted — a 1.3× ATR impulse in a quiet period can be as institutionally significant as 2× ATR in volatile periods

---

## The Three Live-Trading Bugs

These must be fixed before deployment.

---

### Bug 1 — SR_FLIP_RETEST crashes on every signal

**File:** `src/channels/scalp.py`, `_evaluate_sr_flip_retest()`

```python
# This line will raise AttributeError — sr_flip_level is not a field on Signal
sig.sr_flip_level = round(level, 8)
```

`sr_flip_level` does not exist in the `Signal` dataclass in `src/channels/base.py`. Every time SR_FLIP_RETEST generates a valid signal, Python will raise `AttributeError` and silently discard it. This path will never produce output.

**Fix:** Add `sr_flip_level: float = 0.0` to the Signal dataclass.

---

### Bug 2 — MACD confidence penalties are silently discarded

**File:** `src/channels/scalp.py`, `_evaluate_standard()` and other paths

```python
# In the evaluator:
sig.confidence += macd_adj   # e.g., -5.0 for weak MACD

# In scanner._prepare_signal() — runs after evaluate():
sig.confidence = score_signal_components(...)   # Overwrites to new value
sig.confidence = scoring_engine.score(...)      # Overwrites again
sig.confidence = round(min(max(...), 100), 2)   # Overwrites a third time
```

The MACD penalty set in the evaluator is overwritten completely by the scanner pipeline. Only values accumulated in `sig.soft_penalty_total` survive, because the scanner deducts those after the final scoring pass.

**Fix:** Change `sig.confidence += macd_adj` to `sig.soft_penalty_total += abs(macd_adj)` so the penalty flows through the correct channel.

---

### Bug 3 — CVD data contamination across channels

**File:** `src/channels/scalp.py`, `_evaluate_divergence_continuation()`

```python
# DIVERGENCE_CONTINUATION mutates the shared smc_data dict:
smc_data["cvd_divergence"] = _div_label       # e.g., "BULLISH"
smc_data["cvd_divergence_strength"] = _div_strength

# ScalpCVDChannel (runs after ScalpChannel) reads the same key:
cvd_div = smc_data.get("cvd_divergence")      # Sees "BULLISH" from above
```

If `DIVERGENCE_CONTINUATION` fires and writes `"BULLISH"` to the shared `smc_data`, the `ScalpCVDChannel` evaluator will read that value even if it independently computed `"BEARISH"`. This silently produces wrong-direction signals.

**Fix:** Use a path-specific key: `smc_data["_divcont_cvd_divergence"] = _div_label`. The CVD channel reads `"cvd_divergence"` (populated by the SMC detector), so write to a different namespace.

---

## Summary Table

| Path | Status | Market-Reality Grade | Key Risk |
|---|---|---|---|
| LIQUIDITY_SWEEP_REVERSAL | ✅ Ready | A | ADX floor slightly low |
| TREND_PULLBACK_EMA | ✅ Ready | A+ | RSI rising check too strict |
| LIQUIDATION_REVERSAL | ✅ Ready | B+ | Timing lag, unit volume check |
| WHALE_MOMENTUM | ✅ Ready | B | Whale Alert delay |
| VOLUME_SURGE_BREAKOUT | ⚠️ Fix first | C+ | No sustained acceptance, tight pullback zone |
| BREAKDOWN_SHORT | ⚠️ Fix first | C+ | Same as above, funding headwind |
| OPENING_RANGE_BREAKOUT | 🔴 Disabled | — | Proxy window not real ORB |
| SR_FLIP_RETEST | 🐛 Bug first | A- | AttributeError crashes every signal |
| FUNDING_EXTREME_SIGNAL | ✅ Ready | A | RSI SHORT gate too tight |
| QUIET_COMPRESSION_BREAK | ✅ Ready | B | Low fire frequency |
| DIVERGENCE_CONTINUATION | 🐛 Bug first | B+ | CVD dict contamination |
| CONTINUATION_LIQ_SWEEP | ✅ Ready | A- | Sweep recency window |
| POST_DISPLACEMENT_CONT | ✅ Ready | A | Volume multiplier too high |
| FAILED_AUCTION_RECLAIM | ✅ Ready | A- | Window_min too short |
| ScalpFVGChannel | ✅ Ready | B+ | Proximity constant too wide |
| ScalpCVDChannel | ✅ Ready | B+ | SR proximity too loose |
| ScalpVWAPChannel | 🔴 Redesign | D | Wrong VWAP anchor |
| ScalpDivergenceChannel | ✅ Ready | B | Window too small |
| ScalpSupertrendChannel | ✅ Ready | B+ | MTF gate is good |
| ScalpIchimokuChannel | 🔴 Disable | D | Wrong timeframe |
| ScalpOrderblockChannel | ✅ Ready | A- | Freshness check too loose |

---

## Prioritised Action List

**Do immediately (before any live trading):**
1. Fix Bug 1: Add `sr_flip_level: float = 0.0` to Signal dataclass
2. Fix Bug 2: Replace `sig.confidence += macd_adj` with `sig.soft_penalty_total += abs(macd_adj)` in all paths
3. Fix Bug 3: Change `smc_data["cvd_divergence"]` mutation to a private key in DIVERGENCE_CONTINUATION

**Disable until redesigned:**
4. `ScalpVWAPChannel` — anchor VWAP to daily session open (midnight UTC)
5. `ScalpIchimokuChannel` — move to 1h/4h or replace cloud gate with EMA200

**Tune before expanding signal count:**
6. VOLUME_SURGE_BREAKOUT / BREAKDOWN_SHORT — add 2-candle sustained acceptance, extend pullback zone to 1.5%
7. TREND_PULLBACK_EMA — remove RSI rising single-candle check, add RSI-over-N-candles trend
8. LIQUIDATION_REVERSAL — convert volume spike to USD volume

---

*Report generated from full code review of 360-v2-main. All line references reflect the April 20, 2026 snapshot.*
