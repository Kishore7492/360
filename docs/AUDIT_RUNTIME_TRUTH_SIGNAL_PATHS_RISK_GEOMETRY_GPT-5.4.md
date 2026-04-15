# Runtime Truth Audit — Signal Paths, Suppression, and Risk Geometry

- Repository: `mkmk749278/360-v2`
- Branch audited: `main`
- Runtime evidence source: `refs/heads/monitor-logs:monitor/latest.txt` (generated 2026-04-15 05:03:47 UTC)
- Model: `GPT-5.4`
- Scope: requirements-first audit of whether the current runtime actually behaves like a serious multi-pair institutional crypto signal engine, and why only a narrow subset of paths has expressed live while many others remain silent or suppressed.

## Evidence standard used

- **Confirmed evidence** = current code, current docs, current tests, or current monitor output.
- **Strong inference** = best explanation supported by multiple confirmed facts.
- **Open uncertainty** = missing telemetry or evidence not present in repo/runtime artifacts.

---

## 1) Requirements-first architecture truth

### What the system should be in reality

A serious multi-pair crypto signal engine should be **pair-first, regime-aware, and globally context-aware without being globally dominated**.

The strongest production-grade design is:

1. **Pair-local structure is primary**
   - Each pair should have its own market structure, volatility state, liquidity quality, and trigger confirmation.
   - Entry logic should be decided first by the pair's own tape, own structure, and own setup family.

2. **Global market regime is secondary context, not primary thesis**
   - Global market state should adjust aggressiveness, sizing, or confidence.
   - It should not flatten fundamentally different setup families into one uniform gate stack.

3. **BTC context should be an overlay, not the market-definition engine**
   - BTC should matter for correlation-sensitive alts and macro shock conditions.
   - BTC should not substitute for pair-local structure on unrelated or low-correlation names.

4. **Correlation-aware logic must be pair-specific**
   - Highly BTC-correlated alts should be gated differently from low-correlation names.
   - Correlation should be directional, measured, and family-aware.

5. **Family-aware gating is mandatory**
   - Trend-following, reversal, funding, liquidation, quiet-compression, FVG, divergence, and orderblock paths should not all face the same generic MTF / regime / scoring geometry assumptions.
   - Setup-family intent must survive downstream handling.

### Direct answers

#### Should market structure be judged per pair, globally, BTC-led, or hybrid?

**Real requirement:** hybrid, but **pair-local first**. Pair-local structure should decide whether a setup exists. Global regime and BTC context should modulate risk and confidence, not replace pair-local truth.

**Current implementation:** hybrid, but only partially pair-first.
- Pair-local regime is computed from each symbol's own candles in `_build_scan_context()` and `classify_market_state()` (`src/scanner/__init__.py:1566-1660`, `src/signal_quality.py:472-510`).
- BTC/ETH macro context is injected through cross-asset gating and rolling BTC correlation (`src/scanner/__init__.py:1230-1270`, `2316-2349`; `src/cross_asset.py:134-235`).
- Scanner also stores a rolling overall market regime using BTC as the representative benchmark (`src/scanner/__init__.py:1571-1574`).

**Gap:** pair-local analysis exists, but downstream gating is still too uniform and too benchmark-shaped.

#### What is the correct relationship between pair-local structure, global market regime, BTC context, correlation-aware logic, and family-aware gating?

**Real requirement:**
- Pair-local structure = primary truth
- Global regime = secondary market backdrop
- BTC context = macro overlay
- Correlation logic = pair-specific directional modifier
- Family-aware gating = translator between thesis and protection logic

**Current implementation:**
- Pair-local structure exists.
- Global/shared gate policy is highly uniform across channels: all scalp-family channels use the same gate profile with all gates on (`src/scanner/__init__.py:331-340`).
- Regime-specific MTF settings are generic by regime, not by family (`src/scanner/__init__.py:299-312`, `2147-2188`).
- Auxiliary channels are hard-skipped in `VOLATILE_UNSUITABLE` before setup-family compatibility can rescue valid volatile families (`src/scanner/__init__.py:1724-1737`), even though `REGIME_SETUP_COMPATIBILITY` explicitly says some volatile setups are valid there (`src/signal_quality.py:324-340`).

**Gap:** the architecture knows about setup families, but the live funnel still applies too much family-agnostic suppression too early.

#### Is the current architecture too generic, too BTC-proxy-led, or too uniform?

**Real requirement:** no.

**Current implementation:** **too uniform**, and secondarily too benchmark-influenced for some alt paths.
- Runtime instantiates a plain `MarketRegimeDetector()`, not the adaptive pair-tier detector (`src/main.py:175-180`; compare `src/regime.py:559-680`).
- All scalp-family channels share the same enabled gate stack.
- MTF gating is one generic scanner gate for all families.
- Cross-asset gating always references BTC/ETH majors.

**Gap:** materially better than a pure BTC-proxy engine, but still not strong pair-first architecture.

#### What would the strongest production-grade architecture look like independent of current code?

- Pair-local regime classification using pair-tier adaptive thresholds at runtime, not just generic thresholds.
- Family-owned MTF policy instead of a single scanner-level MTF choke point.
- Pair-local structure and trigger confirmation before macro/BTC overlays.
- Correlation-aware gating that can soften, boost, or bypass by pair correlation and setup family.
- Downstream risk handling that validates evaluator geometry without rewriting it into generic channel geometry.
- Per-path telemetry at every loss point, including geometry rejects and post-risk/post-predictive distortions.

### Major requirement / implementation / gap summary

| Major point | Real requirement | Current implementation | Gap |
|---|---|---|---|
| Market structure | Pair-local first | Pair-local regime exists | Good base, but not fully pair-first downstream |
| Global regime | Secondary overlay | Used heavily in shared gate logic | Too generic / too uniform |
| BTC context | Macro overlay only | BTC/ETH cross-asset overlay plus BTC representative market regime | Acceptable as overlay, wrong if treated as dominant truth |
| Correlation handling | Pair-specific directional modifier | Rolling BTC correlation exists | Good improvement, but still only BTC/ETH major framework |
| Family-aware gating | Mandatory | Partially present via exemptions and compatibility tables | Early scanner suppression still overrides family truth too often |
| Pair-tier adaptation | Should affect runtime | Adaptive detector exists in code but runtime uses plain detector | Clear architecture gap |

---

## 2) Full signal-path inventory and expression audit

## Runtime path inventory

### 14 internal `360_SCALP` evaluators

`ScalpChannel.evaluate()` runs these 14 internal evaluators (`src/channels/scalp.py:317-354`):

1. `LIQUIDITY_SWEEP_REVERSAL`
2. `TREND_PULLBACK_EMA`
3. `LIQUIDATION_REVERSAL`
4. `WHALE_MOMENTUM`
5. `VOLUME_SURGE_BREAKOUT`
6. `BREAKDOWN_SHORT`
7. `OPENING_RANGE_BREAKOUT`
8. `SR_FLIP_RETEST`
9. `FUNDING_EXTREME_SIGNAL`
10. `QUIET_COMPRESSION_BREAK`
11. `DIVERGENCE_CONTINUATION`
12. `CONTINUATION_LIQUIDITY_SWEEP`
13. `POST_DISPLACEMENT_CONTINUATION`
14. `FAILED_AUCTION_RECLAIM`

### Auxiliary paid paths

Runtime instantiates 8 channels total (`src/main.py:163-173`):
- `360_SCALP`
- `360_SCALP_FVG`
- `360_SCALP_CVD`
- `360_SCALP_VWAP`
- `360_SCALP_DIVERGENCE`
- `360_SCALP_SUPERTREND`
- `360_SCALP_ICHIMOKU`
- `360_SCALP_ORDERBLOCK`

Distinct auxiliary setup identities preserved downstream:
- `FVG_RETEST`
- `FVG_RETEST_HTF_CONFLUENCE`
- `RSI_MACD_DIVERGENCE`
- `SMC_ORDERBLOCK`
- plus non-main channels such as CVD / VWAP / Supertrend / Ichimoku families.

### Free / radar paths relevant to runtime expression

Radar is not dead in current code.
- Scanner evaluates soft-disabled channels in a radar pass (`src/scanner/__init__.py:3136-3195`).
- `main.py` wires `scanner.on_radar_candidate` into `_handle_radar_candidate()` and `FreeWatchService` (`src/main.py:283-293`, `403-448`).
- WATCHLIST preview routing also exists in router for `360_SCALP` (`src/signal_router.py:482-489`, `893-955`).

## Direct live-expression evidence

### Confirmed from runtime history in `monitor/latest.txt`

The persisted signal history in the monitor report shows **38 total recorded signals**, and only **4 setup classes** are confirmed to have expressed live in recorded history:
- `TREND_PULLBACK_EMA` — 18
- `SR_FLIP_RETEST` — 15
- `CONTINUATION_LIQUIDITY_SWEEP` — 4
- `LIQUIDITY_SWEEP_REVERSAL` — 1

Source: `monitor/latest.txt` recent signal history and by-setup summary.

### Confirmed from current last-500-line live funnel

Parsing the current monitor snapshot yields these current candidate/scoring hits:
- `RSI_MACD_DIVERGENCE` reached scoring **47** times, but was pushed to `score_below50` **47** times.
- `LIQUIDITY_SWEEP_REVERSAL` reached scoring **20** times.
- `SR_FLIP_RETEST` reached scoring **14** times.
- `FAILED_AUCTION_RECLAIM` reached scoring **1** time.

Current scoring outcomes visible in the same snapshot:
- `score_below50:RSI_MACD_DIVERGENCE = 47`
- `score_below50:LIQUIDITY_SWEEP_REVERSAL = 13`
- `score_50to64:SR_FLIP_RETEST = 12`
- `score_50to64:LIQUIDITY_SWEEP_REVERSAL = 5`
- `score_65to79:SR_FLIP_RETEST = 2`
- `score_65to79:LIQUIDITY_SWEEP_REVERSAL = 2`
- `score_50to64:FAILED_AUCTION_RECLAIM = 1`

### Direct answer: why have only a small number of paths generated live signals while many others appear absent?

**Strongest evidence-backed explanation:**

1. **Only a few paths are clearly getting through the full funnel at all.** Recorded live history is concentrated in 4 setups.
2. **Current runtime is dominated by a small number of suppressors before path diversity can matter**:
   - `mtf_gate:360_SCALP = 144`
   - `volatile_unsuitable:360_SCALP_FVG = 144`
   - `volatile_unsuitable:360_SCALP_DIVERGENCE = 144`
   - `volatile_unsuitable:360_SCALP_ORDERBLOCK = 144`
   - `pair_quality:spread = 128`
   - `QUIET_SCALP_BLOCK = 67`
3. **Auxiliary channels are active on VPS runtime** (monitor proves FVG/divergence/orderblock are running), but most are being blocked before meaningful expression.
4. **The main channel is still over-governed by generic MTF and quality gates**, so only the few broadest / loosest / most repeat-triggering paths show up.
5. **Telemetry is still incomplete for several internal paths**, so some are not proven dead — but they are runtime-silent in the current evidence window.

### Path-by-path verdict

| Path / Setup | Live expressed? | Evidence source | If not expressed, likely cause | Verdict category | Confidence |
|---|---|---|---|---|---|
| `TREND_PULLBACK_EMA` | Yes | 18 recorded live outcomes in monitor history | N/A | expressed live | High |
| `SR_FLIP_RETEST` | Yes | 15 recorded live outcomes; 14 current candidate hits | N/A; current weak concentration suggests overexpression | expressed live | High |
| `CONTINUATION_LIQUIDITY_SWEEP` | Yes | 4 recorded live outcomes | N/A | expressed live | High |
| `LIQUIDITY_SWEEP_REVERSAL` | Yes, but rare | 1 recorded live outcome; 20 current candidate hits | Mostly dies at scoring / MTF / WATCHLIST bands | expressed live / candidate generated but blocked | High |
| `FAILED_AUCTION_RECLAIM` | No confirmed live | 1 current candidate hit, `score_50to64` | Watchlist-tier suppression plus upstream gating | candidate generated but blocked | Medium |
| `RSI_MACD_DIVERGENCE` | No confirmed live | 47 candidate hits, 47 `score_below50` | Scoring floor + MTF on divergence channel | candidate generated but blocked | High |
| `FVG_RETEST` / `FVG_RETEST_HTF_CONFLUENCE` | No confirmed live | 61 live FVG SL rejection warnings; `volatile_unsuitable` counts | Volatile-unsuitable pre-skip + FVG geometry reject | suppressed by regime/gating; suppressed by downstream SL/risk geometry | High |
| `SMC_ORDERBLOCK` | No confirmed live | `volatile_unsuitable:360_SCALP_ORDERBLOCK = 144` | Channel pre-skip in volatile unsuitable market state | suppressed by regime/gating | High |
| `LIQUIDATION_REVERSAL` | No confirmed live in current evidence | No direct current-history row | Likely genuine rarity plus generic funnel | unclear / insufficient evidence | Medium |
| `WHALE_MOMENTUM` | No confirmed live | No direct current evidence | Specialist rarity plus generic funnel | unclear / insufficient evidence | Medium |
| `VOLUME_SURGE_BREAKOUT` | No confirmed live | No direct current evidence | Likely should benefit from volatility, but still buried under main-channel generic funnel | silent due to architectural defect / insufficient evidence | Medium |
| `BREAKDOWN_SHORT` | No confirmed live | No direct current evidence | Same as above | silent due to architectural defect / insufficient evidence | Medium |
| `OPENING_RANGE_BREAKOUT` | No confirmed live | No direct current evidence | Governance-disabled by doctrine/default; session-specific rarity | disabled by governance / insufficient evidence | Medium |
| `FUNDING_EXTREME_SIGNAL` | No confirmed live | No direct current evidence | Rare trigger + generic funnel | unclear / insufficient evidence | Medium |
| `QUIET_COMPRESSION_BREAK` | No confirmed live | No direct current evidence | Quiet-only specialist; low frequency | unclear / insufficient evidence | Medium |
| `DIVERGENCE_CONTINUATION` | No confirmed live | No direct current evidence | Internal path not visible in current live telemetry; likely obscured by uniform gates | unclear / insufficient evidence | Medium |
| `POST_DISPLACEMENT_CONTINUATION` | No confirmed live | No direct current evidence | Narrow trigger plus generic funnel | unclear / insufficient evidence | Medium |
| `CVD` / `VWAP` / `Supertrend` / `Ichimoku` paths | No confirmed live | No appearance in current runtime evidence | Soft-disabled by runtime env/defaults or not surfacing in current telemetry | disabled by governance / unclear | Medium |

**Bottom line:** only a small number of paths have generated live signals because the runtime is not evenly expressive. It is a narrow-funnel system where pair spread, volatile-unsuitable channel pre-skips, generic MTF gating, and downstream score floors eliminate most path diversity before emission.

---

## 3) End-to-end suppression funnel

## Runtime path traced

1. **Pair scan / context build**
   - `_build_scan_context()` assembles candles, indicators, SMC result/data, spread, pair quality, market state, regime context, funding, and CVD (`src/scanner/__init__.py:1547-1660`).

2. **Channel pre-skip**
   - `_should_skip_channel()` can kill a whole channel before evaluator generation for:
     - pair-quality spread / weak pair quality
     - `VOLATILE_UNSUITABLE` on non-main channels
     - paused channels
     - cooldowns
     - circuit breaker
     - existing active signal
     - low-ADX ranging suppression (`src/scanner/__init__.py:1662-1775`)

3. **Evaluator generation**
   - `ScalpChannel.evaluate()` runs all 14 internal evaluators and returns all non-`None` candidates.

4. **Setup classification**
   - `classify_setup()` maps signal to a setup class and checks channel and regime compatibility (`src/signal_quality.py:685-775`).

5. **Execution quality**
   - `execution_quality_check()` validates anchor proximity / overextension / trigger confirmation (`src/signal_quality.py:778-913`).

6. **Generic scanner gates**
   - MTF
   - VWAP extension
   - kill-zone
   - OI/funding
   - cross-asset
   - spoof
   - volume divergence
   - cluster suppression (`src/scanner/__init__.py:2147-2413`)

7. **Risk plan**
   - `build_risk_plan()` validates / rewrites SL/TP and R:R, then scanner applies those values back onto the signal (`src/scanner/__init__.py:2414-2418`; `src/signal_quality.py:916-1245`).

8. **Predictive adjustment**
   - Predictive engine can adjust TP/SL and confidence **after** risk-plan validation (`src/scanner/__init__.py:2459-2460`; `src/predictive_ai.py:154-203`).

9. **Scoring and post-score penalties**
   - structured scoring
   - post-score soft-penalty reapplication
   - stat filter
   - pair analysis
   - SMC hard gate
   - trend hard gate
   - quiet block
   - watchlist / min-confidence / component floors (`src/scanner/__init__.py:2620-2968`)

10. **Arbitration / enqueue**
   - best same-direction `360_SCALP` candidate wins (`src/scanner/__init__.py:3064-3117`)

11. **Router**
   - watchlist free route or paid route (`src/signal_router.py:482-489`, `620-760`, `893-955`)

12. **Lifecycle tracking**
   - `_active_signals` → `TradeMonitor` → outcome posts / performance recording (`src/trade_monitor.py:540-752`)
   - But lifecycle persistence is incomplete for some terminal paths:
     - `CANCELLED` invalid-SL signals are removed without `_record_outcome()` (`src/trade_monitor.py:592-611`)
     - `SignalRouter.cleanup_expired()` removes expired signals without performance recording (`src/signal_router.py:1168-1205`)

## Where candidates are most commonly lost

### Correct protective behavior
- `pair_quality:spread too wide`
- some `pair_quality:pair quality below threshold`
- circuit breaker / cooldown / existing active-signal locks
- some FVG geometry rejections where structural stop is truly too wide for scalp use

### Over-generic policy
- **scanner-level MTF gate** on all scalp-family paths
- **identical gate profiles** for all scalp-family channels
- **non-main-channel volatile pre-skip** before family compatibility logic can rescue valid volatile families
- **shared score floors** that compress family differences after a generic gate chain

### Implementation defect / architecture defect
- `VOLATILE_UNSUITABLE` pre-skip on non-main channels is stronger than the later family-aware compatibility tables and therefore can contradict them.
- Runtime uses `MarketRegimeDetector()` rather than the adaptive pair-tier detector already present in code.
- Predictive TP/SL adjustment occurs after risk-plan validation, with no second geometry validation pass.

### Missing telemetry / observability gap
- Current monitor strongly surfaces suppressors by channel and a few setup classes, but does **not** provide a full per-path loss ledger across all 14 internal evaluators.
- Several internal paths are therefore not provably dead or alive; they are simply not visible in current runtime evidence.
- Performance history itself has blind spots because some terminal removals do not record outcomes, so “no live expression” and “no persisted outcome” are not always identical truths.

## Important suppressors

- `QUIET_SCALP_BLOCK`
  - correct as a safety mechanism in principle
  - too blunt when paired with a generic upstream funnel

- `mtf_gate:360_SCALP`
  - strongest current main-channel suppressor
  - likely partially valid, but too generic for a family-diverse engine

- `volatile_unsuitable:*`
  - partially healthy in hostile market conditions
  - too strong as a whole-channel pre-skip when some volatile families are explicitly designed for volatility

- `pair_quality:spread`
  - healthy and evidence-backed protection

- `score_below50:*`
  - usually healthy final scoring rejection
  - especially important for divergence channel, which clearly produces candidates but weak ones

- `score_65to79:*` / `score_50to64:*`
  - no longer the old B-tier dead-zone defect for main `360_SCALP`, but still evidence that many candidates survive generation and die in later governance/scoring bands

- router/lifecycle contradictions
  - WATCHLIST routing is now fixed in code, but live post-fix expression is not yet operationally proven because current monitor shows no fresh signal emissions after the latest restart window

---

## 4) SL / TP / risk geometry integrity audit

## Exact handling path

### Where evaluator-authored SL and TP are created

- Evaluators create initial geometry inside their own channel logic or via `build_channel_signal()`.
- `build_channel_signal()` can itself recompute SL from `sl_dist`, compute TP ratios, and structurally adjust SL/TP1 (`src/channels/base.py:359-529`).

### Where evaluator-authored geometry is preserved or rewritten

1. **Immediately in `build_channel_signal()`**
   - even if evaluator passes `sl/tp1/tp2/tp3`, this helper recomputes from `sl_dist` and channel params (`src/channels/base.py:418-461`).
   - that means some evaluator-authored geometry is already normalized into shared helper geometry before scanner risk-plan handling begins.

2. **In `build_risk_plan()`**
   - protected setups reuse evaluator-authored stop and preserved TP geometry (`src/signal_quality.py:966-1104`, `118-129`).
   - non-protected setups are rewritten into generic stop / TP logic.

3. **After risk validation**
   - scanner writes the risk-plan geometry back onto the signal (`src/scanner/__init__.py:2414-2418`, `1837-1847`).

4. **After that, predictive AI may still rewrite geometry**
   - predictive adjustment is applied after risk-plan validation (`src/scanner/__init__.py:2459-2460`).
   - only setups in `_PREDICTIVE_SLTP_BYPASS_SETUPS` are immune (`src/predictive_ai.py:44-56`, `154-172`).

### Where geometry is validated

`build_risk_plan()` validates:
- max SL cap by channel (`src/signal_quality.py:982-1001`)
- near-zero SL rejection (`1003-1031`)
- directional sanity (`1033-1057`)
- too-tight risk distance (`1059-1070`)
- TP direction sanity and R:R (`1078-1237`)

### Where geometry is capped / rejected

- `360_SCALP` max SL cap = **1.5%**
- `360_SCALP_FVG`, `CVD`, `VWAP`, `DIVERGENCE`, `ORDERBLOCK` max SL cap = **1.0%** (`src/signal_quality.py:345-354`)
- FVG evaluator hard-rejects if `sl_dist/close > 2.00%` before scanner risk plan even runs (`src/channels/scalp_fvg.py:180-188`)

## Correlation with live warnings

### Monitor warning counts from current runtime snapshot
- `FVG SL rejected` = **61**
- `SL near-zero rejection` = **16**
- `SL capped for 360_SCALP` = **8**
- repeated FVG rejects are concentrated in `LABUSDT` and `ENJUSDT`

### Interpretation

#### `FVG SL rejected ... > 2.00% max`

This is **not just healthy protection**. It is evidence of a real **setup-family mismatch** between FVG structural stop doctrine and current scalp max-risk doctrine.

- Healthy interpretation: some FVGs really are too wide for scalp use.
- Defect/distortion interpretation: the live system is repeatedly generating FVG structures whose natural stop geometry does not fit the hard 2% family limit, which means evaluator expression is being killed at the family boundary over and over.

The current evidence favors **protective but too harsh / path-misaligned**, not pure defect.

#### `SL capped for 360_SCALP`

This is **mixed**.
- It is protective in intent.
- But it is also direct evidence that downstream risk handling is rewriting a structurally valid evaluator stop into a capped channel stop.

When that happens repeatedly, evaluator-authored structural invalidation is no longer the live invalidation geometry.

#### `SL near-zero rejection`

This is **stronger evidence of downstream distortion**.
- The guard was written partly for micro-cap precision issues.
- But current live example in the monitor is around entry `100.67000000`, not a sub-penny token.
- That means the failure is not just symbol precision; it is a cap/rewrite interaction producing an unnaturally tiny live stop even on normal-priced instruments.

## Direct answers

### Are these warnings evidence of healthy protection?

**Partly.**
- FVG >2% rejects and grossly wide stops are healthy in principle.
- But the frequency and repetition show the current downstream geometry system is not merely protecting; it is also suppressing method expression materially.

### Or evidence of downstream distortion / geometry defects?

**Also yes.**
The strongest evidence-backed distortion is:
- risk plan validates geometry,
- scanner applies it,
- predictive AI can then still rewrite geometry afterward,
- and there is no second validation pass.

That is architecture truth, not speculation.

### Are there symbol-specific precision issues?

**Some, but not the main story.**
The code explicitly anticipates micro-cap precision problems. But the current live near-zero warning on a ~100 price shows this is not merely a micro-cap precision bug.

### Are there setup-family mismatches?

**Yes, clearly.**
- `FVG_RETEST` is the strongest confirmed family mismatch.
- Non-protected / non-bypassed paths remain exposed to generic downstream distortion.

### Are structurally valid setups being killed incorrectly?

**Probably yes for some classes.**
Most exposed classes:
- `FVG_RETEST` / `FVG_RETEST_HTF_CONFLUENCE`
- `LIQUIDITY_SWEEP_REVERSAL` (not predictive-bypassed)
- `WHALE_MOMENTUM` (not predictive-bypassed)
- auxiliary channel families that are not in the predictive bypass set

## B13 / strategy-expression integrity verdict

- Code now contains real B13-preservation machinery for many internal paths.
- But downstream integrity is **not fully clean** because:
  1. `build_channel_signal()` normalizes evaluator geometry early,
  2. risk-plan caps can replace structural invalidation,
  3. predictive TP/SL scaling can still change post-risk validated geometry for non-bypassed paths.

So current SL/TP handling is **not fully defective**, but it is **partially distorted**.

---

## 5) Regime / market structure truth test

## What runtime actually computes

### Truly pair-level in runtime
- Pair candles / indicators / SMC data
- Pair-local regime classification (`src/scanner/__init__.py:1566-1570`)
- Pair-local market-state classification (`src/signal_quality.py:472-510`)
- Pair-local spread and pair-quality checks
- Pair-local rolling BTC correlation cache (`src/scanner/__init__.py:1230-1270`)

### Global/shared in runtime
- Shared regime detector thresholds (because runtime uses `MarketRegimeDetector`, not pair-tier adaptive runtime detector)
- Shared MTF regime config
- Shared gate profile per channel family
- Shared BTC/ETH macro overlay for cross-asset gate
- Shared same-direction correlated-exposure cap across scalp-family channels

### BTC-led / benchmark-led in runtime
- Scanner stores `_last_market_regime` using BTC as representative benchmark (`src/scanner/__init__.py:1571-1574`)
- Cross-asset gate uses BTC/ETH majors only (`src/scanner/__init__.py:2316-2349`; `src/cross_asset.py:134-235`)

## Direct answer

### Is runtime regime per pair, global, BTC-led, or hybrid?

**Hybrid.**
But it is a **generic hybrid**, not a strong pair-first hybrid.

### Does the live signal pipeline truly analyze per-pair market structure, or is pair-specific structure mostly present only in analytics while runtime logic remains overly generic?

**It does analyze pair-specific structure in runtime.** This is not just offline analytics.

But the deeper truth is:
- pair-specific structure is real at the input stage,
- while the suppression architecture remains too generic at the decision stage.

So the problem is **not** that runtime is fake pair-level.
The problem is that genuine pair-level signals are later forced through overly uniform shared policies.

### Doctrinally wrong even if currently implemented

- Using a plain regime detector at runtime when an adaptive pair-tier detector exists.
- Using one generic MTF choke point for all scalp families.
- Hard-skipping auxiliary channels in `VOLATILE_UNSUITABLE` before family-specific compatibility can work.

---

## 6) Doctrine vs runtime reality

## Confirmed doctrine/runtime matches

- Docs claim WATCHLIST lifecycle admission was fixed by PR #144.
- Current code agrees: router now routes `WATCHLIST` `360_SCALP` signals to free preview only (`src/signal_router.py:482-489`).

## But live operational confirmation is still missing

`OWNER_BRIEF.md` and `docs/ACTIVE_CONTEXT.md` explicitly say live verification is still pending.
That remains true.

Current monitor snapshot shows:
- engine healthy
- zero signals fired in last 200 log lines
- historical recorded signals still dominated by pre-fix low-confidence outcomes

So:
- **docs claim code-level fix** — confirmed
- **docs do not claim fresh runtime proof yet** — also confirmed
- **runtime evidence is still insufficient to prove post-fix operational cleanliness** because the current snapshot contains no fresh emitted paid/live signals after the relevant restart window

## Important contradictions and mismatches

1. **README says top-50 futures; runtime monitor shows `Pairs=75`.**
   - This is a docs/runtime mismatch (`README.md:31-33`; `monitor/latest.txt` scan telemetry lines).

2. **Config defaults disable most auxiliary channels, but runtime monitor proves FVG/divergence/orderblock channels are active.**
   - Code defaults: false in `config/__init__.py:718-730`
   - `.env.example` enables FVG/orderblock/divergence (`.env.example:114-128`)
   - Deploy workflow preserves existing `.env` and only bootstraps from template if missing (`.github/workflows/deploy.yml:85-116`)
   - Runtime evidence: suppressors for those channels in monitor
   - Truth: current live runtime is governed by VPS env state, not config defaults alone.

3. **Architecture doctrine says family-aware refinement is the likely next move; runtime evidence supports that.**
   - `docs/ACTIVE_CONTEXT.md` says targeted family-aware MTF refinement is likely next after lifecycle work.
   - Current monitor still shows `mtf_gate:360_SCALP` as dominant main-path suppressor.
   - This is a doctrine/runtime alignment point, not a contradiction.

4. **Past docs described WATCHLIST contamination as the primary defect; current code says fixed, but fresh runtime proof is absent.**
   - Exact and important distinction: no contradiction, but still incomplete operational proof.

---

## A. Executive verdict

The current runtime is **alive, multi-pair, and genuinely generating some candidates**, but it is **not yet a strongly requirements-aligned pair-first institutional signal engine**.

It is a **partially corrected hybrid architecture** where pair-local structure exists, but most live expression is still being crushed by an overly uniform downstream funnel: pair spread rejection, non-main-channel volatile pre-skips, generic scanner-level MTF gating, quiet-floor suppression, and geometry constraints that sometimes distort evaluator intent.

Only a small subset of paths has confirmed live expression because the runtime is **not equally expressive across its portfolio**. The current system behaves more like a **narrow, over-governed funnel with a few surviving families** than a balanced multi-family institutional engine.

## B. Path expression table

| Path / Setup | Live expressed? | Evidence source | If not expressed, likely cause | Verdict category | Confidence |
|---|---|---|---|---|---|
| `TREND_PULLBACK_EMA` | Yes | 18 historical live outcomes in monitor | N/A | expressed live | High |
| `SR_FLIP_RETEST` | Yes | 15 historical live outcomes; 14 current candidate hits | Current weak concentration suggests widened family | expressed live | High |
| `CONTINUATION_LIQUIDITY_SWEEP` | Yes | 4 historical live outcomes | N/A | expressed live | High |
| `LIQUIDITY_SWEEP_REVERSAL` | Yes, but rare | 1 historical live outcome; 20 current candidate hits | Mostly dies in scoring / watchlist / MTF bands | expressed live / candidate generated but blocked | High |
| `FAILED_AUCTION_RECLAIM` | No confirmed live | 1 current candidate hit, `score_50to64` | Watchlist-tier suppression | candidate generated but blocked | Medium |
| `RSI_MACD_DIVERGENCE` | No confirmed live | 47 current candidate hits, all `score_below50` | Scoring floor + divergence-channel MTF | candidate generated but blocked | High |
| `FVG_RETEST` / `FVG_RETEST_HTF_CONFLUENCE` | No confirmed live | 61 FVG geometry warnings; live `volatile_unsuitable` counts | Volatile pre-skip + geometry reject | suppressed by regime/gating; suppressed by downstream SL/risk geometry | High |
| `SMC_ORDERBLOCK` | No confirmed live | `volatile_unsuitable:360_SCALP_ORDERBLOCK = 144` | Volatile pre-skip | suppressed by regime/gating | High |
| `LIQUIDATION_REVERSAL` | No confirmed live in current evidence | No direct runtime row | Missing telemetry / rarity | unclear / insufficient evidence | Medium |
| `WHALE_MOMENTUM` | No confirmed live in current evidence | No direct runtime row | Missing telemetry / rarity / generic funnel | unclear / insufficient evidence | Medium |
| `VOLUME_SURGE_BREAKOUT` | No confirmed live in current evidence | No direct runtime row | Likely should work in volatility, but generic funnel still dominates | silent due to architectural defect / insufficient evidence | Medium |
| `BREAKDOWN_SHORT` | No confirmed live in current evidence | No direct runtime row | Same as above | silent due to architectural defect / insufficient evidence | Medium |
| `OPENING_RANGE_BREAKOUT` | No confirmed live in current evidence | No direct runtime row | Session rarity; doctrine/default governance limits | disabled by governance / insufficient evidence | Medium |
| `FUNDING_EXTREME_SIGNAL` | No confirmed live in current evidence | No direct runtime row | Rare trigger plus generic funnel | unclear / insufficient evidence | Medium |
| `QUIET_COMPRESSION_BREAK` | No confirmed live in current evidence | No direct runtime row | Quiet-only specialist | unclear / insufficient evidence | Medium |
| `DIVERGENCE_CONTINUATION` | No confirmed live in current evidence | No direct runtime row | Internal path obscured by generic funnel | unclear / insufficient evidence | Medium |
| `POST_DISPLACEMENT_CONTINUATION` | No confirmed live in current evidence | No direct runtime row | Narrow trigger plus generic funnel | unclear / insufficient evidence | Medium |
| `CVD` / `VWAP` / `Supertrend` / `Ichimoku` paths | No confirmed live in current evidence | No runtime expression in monitor | Soft-disabled or not surfacing in current VPS env/telemetry | disabled by governance / unclear | Medium |

## C. Top suppressors table

| Suppressor | What it means | Verdict | Likely impact on expression |
|---|---|---|---|
| `mtf_gate:360_SCALP` | Generic scanner-level MTF hard block on main channel | generic / partially over-harsh | Main reason current main-path diversity stays low |
| `volatile_unsuitable:360_SCALP_FVG` | FVG channel skipped before candidate competition | harsh-but-valid, but over-generic as architecture | Kills FVG paid expression almost entirely |
| `volatile_unsuitable:360_SCALP_DIVERGENCE` | Divergence channel skipped in unsuitable volatile state | harsh-but-valid, but over-generic as architecture | Kills auxiliary divergence diversity |
| `volatile_unsuitable:360_SCALP_ORDERBLOCK` | Orderblock channel skipped in unsuitable volatile state | harsh-but-valid, but over-generic as architecture | Kills orderblock diversity |
| `pair_quality:spread` | Pair spread too wide for scalp execution | healthy | Correctly blocks large parts of universe |
| `QUIET_SCALP_BLOCK` | Quiet-regime confidence floor for scalp | healthy in principle, too blunt in context | Blocks remaining near-threshold survivors |
| `score_below50:RSI_MACD_DIVERGENCE` | Divergence candidates reach scoring but are too weak | healthy | Confirms channel is alive but low quality |
| `score_50to64:*` | Candidate survives but only as WATCHLIST | healthy tiering, but evidence of downstream bottleneck | Shows near-miss expression bands |
| `FVG SL rejected` | FVG structural stop too wide for hard family limit | protective but too harsh / family-misaligned | Strong family-specific loss channel |
| `SL capped` / `SL near-zero rejection` | Downstream risk-plan geometry override / rejection | partially distorted | Can distort evaluator-authored expression |

## D. Architecture verdict

**Partially aligned but still too generic.**

The runtime is not a fake pair-level engine. Pair-local structure is genuinely computed. But the live architecture is still **materially under-optimized for pair-first, family-aware production behavior** because its shared scanner funnel is too uniform and too dominant.

## E. SL / Geometry verdict

**Partially distorted.**

The system has meaningful protective controls and several real B13-preservation mechanisms. But downstream handling still distorts strategy expression in important cases through channel caps, generic rewrites for non-protected setups, and post-risk predictive TP/SL scaling without re-validation.

## F. Best next PR / PR sequence

1. **Family-aware MTF gate refinement on main `360_SCALP`**
   - Highest evidence next move.
   - Current monitor still shows `mtf_gate:360_SCALP` as the dominant main-path suppressor.

2. **Fix volatile pre-skip contradiction for auxiliary channels**
   - Do not pre-kill whole channels in `VOLATILE_UNSUITABLE` when later family compatibility tables already declare some volatile families valid.

3. **Risk-geometry integrity hardening**
   - Re-validate geometry after predictive TP/SL adjustment, or stop predictive scaling on more setup families.
   - Add family-specific telemetry for geometry rewrite vs reject.

4. **FVG-specific geometry doctrine review**
   - Decide whether current repeated `>2%` rejects are correct business exclusion or whether FVG should be re-scoped/re-tiered instead of repeatedly generating doomed candidates.

5. **Per-path observability PR**
   - Add explicit per-setup counters for all 14 internal evaluators at: generated, passed setup, passed execution, passed MTF, passed risk, scored, emitted.
   - This removes the current uncertainty on silent paths.

## G. Requirements vs implementation gap

| What the system should do | What it currently does | What should change next |
|---|---|---|
| Judge structure pair-first with global overlays secondary | Pair-local structure exists, but shared downstream funnel dominates | Make family-aware / pair-aware downstream gating stronger than generic shared gating |
| Use pair-tier adaptive regime logic in runtime | Runtime uses plain `MarketRegimeDetector()` | Switch runtime to adaptive pair-tier regime detection |
| Let volatile-valid families express in volatility | Non-main channels are pre-skipped in `VOLATILE_UNSUITABLE` | Remove or narrow whole-channel volatile pre-skip |
| Preserve evaluator-authored geometry unless truly invalid | Protected setups preserved partly; non-protected setups still rewritten; predictive scaling can distort post-validation | Re-validate after predictive scaling or expand bypass coverage |
| Express a balanced multi-family portfolio | Live expression concentrated in 4 historically expressed setups; current candidates heavily concentrated in few paths | Reduce generic MTF choke point and improve per-path telemetry |
| Use BTC context as overlay, not as dominant market truth | Runtime is hybrid but still benchmark-shaped in cross-asset logic | Keep BTC overlay, but reduce overreach into family-agnostic suppression |
| Make docs match live runtime | README says top-50, runtime shows 75 pairs; config defaults differ from VPS behavior | Update docs/env/runtime documentation to reflect actual deployed truth |
