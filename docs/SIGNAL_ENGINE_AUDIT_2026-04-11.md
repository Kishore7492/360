# 1. Executive judgment

**Bottom line:** the engine is **not yet trustworthy enough to treat as a clean institutional-grade redeploy without one more correction pass**.

The good news:
- the **best core 360_SCALP paths are genuinely solid**: `TREND_PULLBACK_EMA`, `SR_FLIP_RETEST`, `CONTINUATION_LIQUIDITY_SWEEP`, `POST_DISPLACEMENT_CONTINUATION`, `FAILED_AUCTION_RECLAIM`
- `LIQUIDATION_REVERSAL`, `VOLUME_SURGE_BREAKOUT`, `BREAKDOWN_SHORT`, `QUIET_COMPRESSION_BREAK` are at least directionally sound

The bad news:
- the **live engine does not faithfully preserve evaluator intent**
- **path-specific soft penalties are being lost**
- **risk-plan / predictive rewriting distorts evaluator SL/TP design**
- **same-direction dedup inside `360_SCALP` is order-driven, not quality-driven**
- **enabled auxiliary channels (`FVG`, `DIVERGENCE`, `ORDERBLOCK`) are not integrated into the portfolio taxonomy/scoring architecture and are not trustworthy as active production paths**

So this is **not an infra problem**. It is a **strategy-expression integrity problem**.

---

# 2. Full active path inventory

## Enabled by default on `main`

| Path | Default live status | Location |
|---|---|---|
| LIQUIDITY_SWEEP_REVERSAL | active | `src/channels/scalp.py:281` |
| TREND_PULLBACK_EMA | active | `src/channels/scalp.py:530` |
| LIQUIDATION_REVERSAL | active | `src/channels/scalp.py:693` |
| WHALE_MOMENTUM | active | `src/channels/scalp.py:834` |
| VOLUME_SURGE_BREAKOUT | active | `src/channels/scalp.py:985` |
| BREAKDOWN_SHORT | active | `src/channels/scalp.py:1201` |
| OPENING_RANGE_BREAKOUT | active | `src/channels/scalp.py:1423` |
| SR_FLIP_RETEST | active | `src/channels/scalp.py:1569` |
| FUNDING_EXTREME_SIGNAL | active | `src/channels/scalp.py:1846` |
| QUIET_COMPRESSION_BREAK | active | `src/channels/scalp.py:2004` |
| DIVERGENCE_CONTINUATION | active | `src/channels/scalp.py:2156` |
| CONTINUATION_LIQUIDITY_SWEEP | active | `src/channels/scalp.py:2328` |
| POST_DISPLACEMENT_CONTINUATION | active | `src/channels/scalp.py:2585` |
| FAILED_AUCTION_RECLAIM | active | `src/channels/scalp.py:2918` |
| FVG_RETEST (`360_SCALP_FVG`) | active | `src/channels/scalp_fvg.py:44` |
| RSI_MACD_DIVERGENCE (`360_SCALP_DIVERGENCE`) | active | `src/channels/scalp_divergence.py:56` |
| SMC_ORDERBLOCK (`360_SCALP_ORDERBLOCK`) | active | `src/channels/scalp_orderblock.py:132` |

## Soft-disabled by default / effectively not contributing live

| Path | Default live status | Location |
|---|---|---|
| CVD_DIVERGENCE (`360_SCALP_CVD`) | disabled / radar-only | `src/channels/scalp_cvd.py:41` |
| VWAP_BOUNCE (`360_SCALP_VWAP`) | disabled / radar-only | `src/channels/scalp_vwap.py:38` |
| SUPERTREND_FLIP (`360_SCALP_SUPERTREND`) | disabled / radar-only | `src/channels/scalp_supertrend.py:38` |
| ICHIMOKU_TK_CROSS (`360_SCALP_ICHIMOKU`) | disabled / radar-only | `src/channels/scalp_ichimoku.py:30` |

## Explicitly inactive / removed
- `RANGE_FADE` is **not live** and was intentionally removed. Good decision.

---

# 3. Path-by-path audit

## LIQUIDITY_SWEEP_REVERSAL
**Location:** `src/channels/scalp.py:281`

- **Thesis:** reclaim after sweep + momentum + EMA/MACD/MTF support
- **Regime fit:** broadly acceptable; strongest in trend/expansion, less compelling in quiet/range
- **SL review:** good; using swept level with buffer is thesis-valid
- **TP review:** evaluator TP is coherent enough, but live risk-plan rewrites it into generic reversal targets
- **Scanner/funnel review:** mostly treated correctly; big problem is same-direction ordering inside `360_SCALP`, so this path can block later better ideas or be blocked by earlier mediocre ones
- **Business-quality judgment:** coherent, useful, not elite-pure but solid
- **Deploy verdict:** **Good but needs refinement**
- **Recommended action:** keep active; preserve evaluator TP/penalty intent and stop order-based same-direction dedup

## TREND_PULLBACK_EMA
**Location:** `src/channels/scalp.py:530`

- **Thesis:** trend continuation on EMA pullback with candle rejection
- **Regime fit:** correct; trend-only
- **SL review:** acceptable; EMA21-based stop is sensible, though slightly indicator-led rather than structural
- **TP review:** fine in evaluator; live risk-plan rewrite is acceptable but less path-specific
- **Scanner/funnel review:** **likely overblocked by the SMC hard gate**; this path only requires FVG/OB support, but downstream SMC scoring heavily rewards sweep/MSS, which this thesis does not need
- **Business-quality judgment:** one of the better core paths
- **Deploy verdict:** **Strong / trust for redeploy**
- **Recommended action:** keep active; fix SMC overblocking before redeploy

## LIQUIDATION_REVERSAL
**Location:** `src/channels/scalp.py:693`

- **Thesis:** cascade exhaustion + CVD divergence + RSI extreme + volume spike + nearby structure
- **Regime fit:** good in volatile / panic / dirty range; architecturally sensible
- **SL review:** good; beyond cascade extremum matches thesis
- **TP review:** evaluator defers to downstream generic mean-reversion plan; acceptable but not elegant
- **Scanner/funnel review:** well treated; correctly exempt from trend/SMC hard-gate logic
- **Business-quality judgment:** genuinely useful specialist-support path
- **Deploy verdict:** **Good but needs refinement**
- **Recommended action:** keep active; preserve path-specific TP logic if you want cleaner institutional expression

## WHALE_MOMENTUM
**Location:** `src/channels/scalp.py:834`

- **Thesis:** whale/tick-flow impulse confirmed by order-book imbalance
- **Regime fit:** makes sense in fast/volatile conditions
- **SL review:** weak-to-acceptable; pure ATR stop, not order-flow invalidation
- **TP review:** generic momentum-style, not thesis-shaped
- **Scanner/funnel review:** **architecturally problematic**:
  - path-level OBI/RSI penalties are written in evaluator
  - scanner later overwrites `soft_penalty_total`
  - path is trend-gate exempt, but **not SMC-gate exempt**, which is wrong for an order-flow impulse thesis
- **Business-quality judgment:** interesting path, but currently under-integrated and too fragile
- **Deploy verdict:** **Usable but questionable**
- **Recommended action:** either integrate it properly (preserve penalties + exempt from irrelevant SMC gate) or demote it

## VOLUME_SURGE_BREAKOUT
**Location:** `src/channels/scalp.py:985`

- **Thesis:** real breakout on surge volume, entered on pullback/retest
- **Regime fit:** correct in trend/expansion/volatile contexts; blocked in quiet
- **SL review:** good; below breakout level is thesis-valid
- **TP review:** evaluator measured-move TP is good; **live engine rewrites it to generic breakout RR**
- **Scanner/funnel review:** mostly correct; properly exempt from SMC sweep requirement
- **Business-quality judgment:** good core breakout path
- **Deploy verdict:** **Good but needs refinement**
- **Recommended action:** keep active; preserve measured-move TP instead of generic risk-plan rewrite

## BREAKDOWN_SHORT
**Location:** `src/channels/scalp.py:1201`

- **Thesis:** bearish mirror of surge breakout; breakdown then dead-cat bounce short
- **Regime fit:** correct; strong in bearish expansion/volatile conditions
- **SL review:** good; above broken level
- **TP review:** evaluator measured-move logic is good; same downstream rewrite problem
- **Scanner/funnel review:** broadly correct
- **Business-quality judgment:** strong directional core path
- **Deploy verdict:** **Good but needs refinement**
- **Recommended action:** keep active; preserve evaluator TP geometry

## OPENING_RANGE_BREAKOUT
**Location:** `src/channels/scalp.py:1423`

- **Thesis:** session opening-range breakout
- **Regime fit:** intended fit is fine; implementation fit is not
- **SL review:** acceptable
- **TP review:** acceptable measured-range style
- **Scanner/funnel review:** main issue is not funnel; it is the evaluator itself
- **Business-quality judgment:** **weakest of the active internal 360_SCALP paths**
- **Why weak:** it does **not** build the actual session opening range; it uses the last 8 bars as a proxy whenever the current UTC hour is London/NY. That is not institutional-grade session logic.
- **Deploy verdict:** **Weak / should be reconsidered**
- **Recommended action:** refine before redeploy or temporarily remove from active portfolio

## SR_FLIP_RETEST
**Location:** `src/channels/scalp.py:1569`

- **Thesis:** broken level flips role, current candle retests with rejection
- **Regime fit:** very good; meaningful in trend, weak trend, range, expansion; blocked in full volatility
- **SL review:** strong; beyond flipped level is thesis-valid
- **TP review:** evaluator and risk-plan are both broadly coherent
- **Scanner/funnel review:** treated well; exempt from SMC hard gate, which is correct
- **Business-quality judgment:** one of the cleanest business-grade paths in the engine
- **Deploy verdict:** **Strong / trust for redeploy**
- **Recommended action:** keep active

## FUNDING_EXTREME_SIGNAL
**Location:** `src/channels/scalp.py:1846`

- **Thesis:** contrarian entry when funding is extreme and price/order-flow start normalizing
- **Regime fit:** acceptable in trend/range/expansion, but not quiet
- **SL review:** acceptable; liquidation-cluster anchor is sensible when available
- **TP review:** **weakest TP design among active internal paths**; TP1 is a fixed 0.5% normalization move and feels placeholder-like
- **Scanner/funnel review:** trend/SMC exemptions are correct; path itself is the weaker part
- **Business-quality judgment:** not bad, but not strong enough to call institutional-grade yet
- **Deploy verdict:** **Usable but questionable**
- **Recommended action:** keep only if you want specialist diversity; otherwise deprioritize until TP/thesis calibration is improved

## QUIET_COMPRESSION_BREAK
**Location:** `src/channels/scalp.py:2004`

- **Thesis:** genuine squeeze release in quiet/ranging conditions
- **Regime fit:** correct and narrow
- **SL review:** good; opposite band invalidation fits thesis
- **TP review:** evaluator TP based on band width is coherent; downstream generic breakout TP is less coherent
- **Scanner/funnel review:** quiet exemption is correct; this is the one path that should survive quiet filters
- **Business-quality judgment:** good specialist path
- **Deploy verdict:** **Good but needs refinement**
- **Recommended action:** keep active; preserve band-width TP logic

## DIVERGENCE_CONTINUATION
**Location:** `src/channels/scalp.py:2156`

- **Thesis:** hidden CVD divergence supports continuation in an existing trend
- **Regime fit:** correct; trend-only
- **SL review:** acceptable but not ideal; EMA21 stop is generic for a divergence thesis
- **TP review:** decent
- **Scanner/funnel review:** mixed:
  - correctly exempt from SMC hard gate
  - likely under-scored because downstream PR09 thesis logic relies on shared `cvd_divergence` metadata, while this evaluator computes divergence locally
- **Business-quality judgment:** good support path, but under-modeled
- **Deploy verdict:** **Good but needs refinement**
- **Recommended action:** keep active; align scorer with evaluator’s actual divergence evidence

## CONTINUATION_LIQUIDITY_SWEEP
**Location:** `src/channels/scalp.py:2328`

- **Thesis:** trend continuation after recent liquidity sweep and reclaim
- **Regime fit:** excellent; trend/expansion only
- **SL review:** strong; beyond swept level with ATR buffer is thesis-valid
- **TP review:** solid; FVG/swing/fallback is coherent
- **Scanner/funnel review:** one of the better-treated paths; should keep SMC requirement
- **Business-quality judgment:** strong institutional-style continuation path
- **Deploy verdict:** **Strong / trust for redeploy**
- **Recommended action:** keep active

## POST_DISPLACEMENT_CONTINUATION
**Location:** `src/channels/scalp.py:2585`

- **Thesis:** displacement -> tight absorption -> re-acceleration
- **Regime fit:** excellent
- **SL review:** evaluator SL is strong; return into consolidation is the correct invalidation
- **TP review:** evaluator measured-move off displacement height is strong
- **Scanner/funnel review:** evaluator is good; **downstream risk-plan is the problem** because it can replace the structural stop/targets with generic logic
- **Business-quality judgment:** one of the best raw evaluator designs in the repo
- **Deploy verdict:** **Good but needs refinement**
- **Recommended action:** keep active; preserve evaluator SL/TP in live dispatch

## FAILED_AUCTION_RECLAIM
**Location:** `src/channels/scalp.py:2918`

- **Thesis:** failed acceptance beyond obvious level, then reclaim back inside structure
- **Regime fit:** excellent; especially clean range / weak trend / breakout-failure contexts
- **SL review:** **best SL design in the engine**
- **TP review:** very good; measured off the failed-auction tail and reclaim structure
- **Scanner/funnel review:** mostly correct; risk-plan explicitly preserves this path’s structural stop better than others
- **Business-quality judgment:** genuinely business-grade
- **Deploy verdict:** **Strong / trust for redeploy**
- **Recommended action:** keep active and treat as a top-tier support path

## FVG_RETEST (`360_SCALP_FVG`)
**Location:** `src/channels/scalp_fvg.py:44`

- **Thesis:** retest of unfilled FVG
- **Regime fit:** raw evaluator thesis is acceptable
- **SL review:** evaluator SL has thoughtful age/fill decay, but starts to look fake-precise
- **TP review:** generic RR, not great
- **Scanner/funnel review:** **badly distorted live**
  - path is enabled
  - but it is **not self-classifying**
  - downstream scanner overwrites its `setup_class` and `analyst_reason`
  - it is not part of active portfolio-role taxonomy
  - generic SMC gate can overblock it
- **Business-quality judgment:** not trustworthy as currently integrated
- **Deploy verdict:** **Weak / should be reconsidered**
- **Recommended action:** disable before redeploy unless you fully integrate it into setup taxonomy/scoring/risk logic

## RSI_MACD_DIVERGENCE (`360_SCALP_DIVERGENCE`)
**Location:** `src/channels/scalp_divergence.py:56`

- **Thesis:** RSI/MACD divergence scalp
- **Regime fit:** it tries to avoid strong trends, but this is still mostly indicator divergence logic
- **SL review:** generic ATR stop, not structurally convincing
- **TP review:** generic RR
- **Scanner/funnel review:** same structural problem as FVG:
  - enabled
  - not self-classifying
  - no portfolio role
  - overwritten by generic downstream setup classification
- **Business-quality judgment:** **retail-style compared with the newer core 360_SCALP paths**
- **Deploy verdict:** **Weak / should be reconsidered**
- **Recommended action:** disable or demote; do not treat as institutional-grade active alpha

## SMC_ORDERBLOCK (`360_SCALP_ORDERBLOCK`)
**Location:** `src/channels/scalp_orderblock.py:132`

- **Thesis:** fresh order-block retest
- **Regime fit:** acceptable in theory
- **SL review:** evaluator SL is acceptable
- **TP review:** generic RR
- **Scanner/funnel review:** again not properly integrated into live setup taxonomy; freshness detection is simplistic and can mislabel random impulsive candles as OBs
- **Business-quality judgment:** more plausible than divergence channel, but still not live-business-grade in current form
- **Deploy verdict:** **Usable but questionable**
- **Recommended action:** either properly integrate or remove from active defaults

## CVD_DIVERGENCE (`360_SCALP_CVD`)
**Location:** `src/channels/scalp_cvd.py:41`

- **Thesis:** acceptable
- **Live status:** disabled by default
- **Funnel/live contribution:** effectively inactive; radar-only path is unlikely to contribute meaningfully
- **Deploy verdict:** **Effectively inactive / blocked / not contributing**
- **Recommended action:** keep disabled unless fully integrated

## VWAP_BOUNCE (`360_SCALP_VWAP`)
**Location:** `src/channels/scalp_vwap.py:38`

- **Thesis:** mean reversion to VWAP bands
- **Live status:** disabled by default
- **Business judgment:** coherent but lower-grade relative to the newer structure-driven paths
- **Deploy verdict:** **Effectively inactive / blocked / not contributing**
- **Recommended action:** keep disabled

## SUPERTREND_FLIP (`360_SCALP_SUPERTREND`)
**Location:** `src/channels/scalp_supertrend.py:38`

- **Thesis:** indicator flip
- **Live status:** disabled by default
- **Business judgment:** retail-style, indicator-led, not institutional-grade
- **Deploy verdict:** **Effectively inactive / blocked / not contributing**
- **Recommended action:** keep disabled

## ICHIMOKU_TK_CROSS (`360_SCALP_ICHIMOKU`)
**Location:** `src/channels/scalp_ichimoku.py:30`

- **Thesis:** indicator cross with cloud filter
- **Live status:** disabled by default
- **Business judgment:** cleaner than Supertrend, still indicator-led and not part of current institutional portfolio design
- **Deploy verdict:** **Effectively inactive / blocked / not contributing**
- **Recommended action:** keep disabled

---

# 4. Cross-path findings

## Strongest paths
1. `FAILED_AUCTION_RECLAIM`
2. `CONTINUATION_LIQUIDITY_SWEEP`
3. `SR_FLIP_RETEST`
4. `TREND_PULLBACK_EMA`
5. `POST_DISPLACEMENT_CONTINUATION` *(raw evaluator strong; live risk handling weakens it)*

## Weakest active paths
1. `OPENING_RANGE_BREAKOUT`
2. `RSI_MACD_DIVERGENCE`
3. `FVG_RETEST` *(as a live integrated path, not as a raw idea)*
4. `WHALE_MOMENTUM`
5. `FUNDING_EXTREME_SIGNAL`

## Best SL design
- `FAILED_AUCTION_RECLAIM`
- `CONTINUATION_LIQUIDITY_SWEEP`
- `POST_DISPLACEMENT_CONTINUATION`
- `SR_FLIP_RETEST`

## Weakest SL design
- `WHALE_MOMENTUM`
- `DIVERGENCE_CONTINUATION`
- `RSI_MACD_DIVERGENCE`
- `VWAP_BOUNCE` / other disabled legacy indicator channels

## Best TP design
- `VOLUME_SURGE_BREAKOUT`
- `BREAKDOWN_SHORT`
- `FAILED_AUCTION_RECLAIM`
- `POST_DISPLACEMENT_CONTINUATION`

## Weakest TP design
- `FUNDING_EXTREME_SIGNAL`
- `WHALE_MOMENTUM`
- enabled auxiliary channels using generic RR only

## Paths likely overblocked
- `TREND_PULLBACK_EMA` via downstream SMC hard gate
- `WHALE_MOMENTUM` via downstream SMC hard gate despite non-SMC thesis
- `FAILED_AUCTION_RECLAIM` via downstream trend gate
- auxiliary enabled channels because scanner does not preserve their true setup identity
- all later `360_SCALP` same-direction paths because first accepted candidate wins by **method order**, not quality

## Paths likely too noisy
- `RSI_MACD_DIVERGENCE`
- `SMC_ORDERBLOCK`
- `OPENING_RANGE_BREAKOUT`
- `WHALE_MOMENTUM` when order-book confirmation is missing

## Duplicated / overlapping paths
- `LIQUIDITY_SWEEP_REVERSAL`, `CONTINUATION_LIQUIDITY_SWEEP`, `FAILED_AUCTION_RECLAIM`, `SR_FLIP_RETEST` all live in nearby structural territory
- `VOLUME_SURGE_BREAKOUT`, `OPENING_RANGE_BREAKOUT`, `POST_DISPLACEMENT_CONTINUATION` overlap around expansion continuation
- enabled auxiliary `FVG_RETEST` and `SMC_ORDERBLOCK` overlap heavily with `TREND_PULLBACK_EMA` and `SR_FLIP_RETEST`

## Scoring inconsistencies
- evaluator-level `soft_penalty_total` is being overwritten by scanner-level soft penalty bookkeeping
- many evaluator-designed SL/TP plans are overwritten downstream by generic risk-plan logic
- predictive AI then adjusts TP/SL again using a generic heuristic
- `360_SCALP` B-quality signals in the **65-79** zone are hard-blocked by channel minimums, while weaker `50-64` WATCHLIST signals can still survive as watchlist alerts
- enabled auxiliary channels are not part of `ACTIVE_PATH_PORTFOLIO_ROLES` and are not preserved as distinct setup classes downstream

## Portfolio-role inconsistencies
- core/support/specialist taxonomy exists only for the newer internal `360_SCALP` paths
- enabled auxiliary channels are **active in production defaults but absent from the formal portfolio design**
- that is not institutional-grade portfolio governance

## Architecturally unfinished / suspicious areas
- same-direction dedup inside `360_SCALP` is sequence-biased
- radar pass for soft-disabled channels is close to meaningless because raw evaluator outputs are unscored
- removed `RANGE_FADE` still leaves legacy references in classification/scoring paths
- path-specific validity windows are flattened back to channel defaults

---

# 5. Pre-redeploy action list

## 1. Must be corrected before fresh VPS reinstall/deploy
1. **Fix path-integrity architecture**
   - preserve evaluator `soft_penalty_total`
   - preserve evaluator setup identity where intended
   - stop generic downstream overwriting from corrupting path intent
2. **Fix same-direction `360_SCALP` dedup**
   - evaluate all same-direction candidates first
   - rank by final scored quality
   - only then dedup
3. **Decide the fate of enabled auxiliary channels**
   - either fully integrate `FVG_RETEST`, `RSI_MACD_DIVERGENCE`, `SMC_ORDERBLOCK`
   - or disable them before redeploy
4. **Stop risk-plan/predictive rewriting from distorting strong evaluator paths**
   - especially `PDC`, `SURGE`, `BREAKDOWN`, `QUIET_COMPRESSION_BREAK`, `TREND_PULLBACK_EMA`
5. **Fix gate alignment**
   - `TREND_PULLBACK_EMA` likely needs SMC-gate reconsideration
   - `WHALE_MOMENTUM` likely needs SMC treatment reconsideration
   - `FAILED_AUCTION_RECLAIM` likely needs trend-gate reconsideration

## 2. Should ideally be refined before redeploy
1. Rebuild `OPENING_RANGE_BREAKOUT` to use a real session opening range
2. Improve `FUNDING_EXTREME_SIGNAL` TP logic
3. Make `DIVERGENCE_CONTINUATION` scoring reflect its real divergence evidence
4. Revisit `WHALE_MOMENTUM` stop logic so it is not just ATR-based

## 3. Can wait until after fresh deployment
1. clean up residual `RANGE_FADE` references
2. improve setup labels / taxonomy consistency for messaging
3. improve radar architecture for soft-disabled channels
4. refine validity-window handling

## 4. Paths safest to trust immediately after a clean deploy
If you were forced to deploy with minimal change, the safest relative bets are:
- `FAILED_AUCTION_RECLAIM`
- `CONTINUATION_LIQUIDITY_SWEEP`
- `SR_FLIP_RETEST`
- `TREND_PULLBACK_EMA`
- `LIQUIDATION_REVERSAL`

But even these are being expressed through a distorted downstream pipeline, so “safe” here is only relative.

---

# 6. Final deploy recommendation

## **Redeploy only after one more correction pass**

**Why:**
- the core engine has **real promise**
- several internal paths are **good enough to keep**
- but the **live production expression is not faithful enough yet**
- the current engine still mixes:
  - strong institutional-style internal paths
  - weak/legacy auxiliary active paths
  - downstream score/risk rewrites that blur path intent
  - order-biased dedup that can suppress the best setup and keep the first one

That is not the standard for a business-critical fresh deployment whose goal is **high-quality, trustworthy signals**.

**Business answer:**  
Do **one more correction pass first**.  
Do **not** reinstall and redeploy this exact signal engine as-is and call it trusted.
