# Path Expression Research Report

- Repository: `mkmk749278/360-v2`
- Research date: `2026-04-14`
- Model/agent identifier used: `advanced GitHub Copilot Task Agent`
- Identifier accuracy: best-available agent identifier exposed in-session; exact underlying model name was not exposed.

## Executive summary

**Confirmed code facts**
- The repository contains a broad path inventory, but the live paid/persisted path inventory is much narrower in practice because only `360_SCALP` is enabled by default; every auxiliary scalp-family channel is soft-disabled in config and only participates in the radar/watch flow unless explicitly re-enabled (`config/__init__.py:718-735`, `src/scanner/__init__.py:3136-3195`).
- A candidate only reaches `data/signal_performance.json` if it survives scanner gates, router gates, is posted as a real routed signal, enters `TradeMonitor`, and then reaches a terminal lifecycle outcome that calls `PerformanceTracker.record_outcome()` (`src/scanner/__init__.py:2072-2972`, `src/signal_router.py:482-769`, `src/trade_monitor.py:219-328`, `src/performance_tracker.py:92-151`).
- Current code routes `360_SCALP` `WATCHLIST` (`50-64`) to a free preview path and returns before paid routing / active lifecycle registration (`src/signal_router.py:482-489`, `src/signal_router.py:896-955`).
- The fetched live monitor snapshot still shows persisted low-confidence history dominated by `TREND_PULLBACK_EMA`, `SR_FLIP_RETEST`, and `CONTINUATION_LIQUIDITY_SWEEP`, with only one recent `LIQUIDITY_SWEEP_REVERSAL` outside that cluster (`origin/monitor-logs:monitor/latest.txt:75-127`).

**Realistic operational inference**
- The most realistic explanation for the current narrow persisted path diversity is **not one thing**. It is a combination of: default channel disablement, heavy scanner suppressors, same-direction arbitration, router staleness/correlation/cooldown filters, persistence only on terminal outcomes, and likely **historical contamination from older runtime behavior** that allowed low-confidence paths into persisted history before the current watchlist segregation code landed.
- Several path families are implemented but are probably under-expressing operationally because they are either disabled, radar-only, naming-drifted, structurally reclassified downstream, or too heavily filtered to survive to persistence.

---

## 1. Path/setup inventory

### Confirmed code facts

#### Canonical `SetupClass` families
Defined in `src/signal_quality.py:18-45`:

- `TREND_PULLBACK_CONTINUATION`
- `TREND_PULLBACK_EMA`
- `BREAKOUT_RETEST`
- `LIQUIDITY_SWEEP_REVERSAL`
- `LIQUIDATION_REVERSAL`
- `RANGE_REJECTION`
- `MOMENTUM_EXPANSION`
- `EXHAUSTION_FADE`
- `RANGE_FADE`
- `WHALE_MOMENTUM`
- `MULTI_STRATEGY_CONFLUENCE`
- `VOLUME_SURGE_BREAKOUT`
- `BREAKDOWN_SHORT`
- `OPENING_RANGE_BREAKOUT`
- `SR_FLIP_RETEST`
- `FUNDING_EXTREME_SIGNAL`
- `QUIET_COMPRESSION_BREAK`
- `DIVERGENCE_CONTINUATION`
- `CONTINUATION_LIQUIDITY_SWEEP`
- `POST_DISPLACEMENT_CONTINUATION`
- `FAILED_AUCTION_RECLAIM`
- `FVG_RETEST`
- `FVG_RETEST_HTF_CONFLUENCE`
- `RSI_MACD_DIVERGENCE`
- `SMC_ORDERBLOCK`

#### Canonical portfolio-intent families
`ACTIVE_PATH_PORTFOLIO_ROLES` marks the main production intent as:
- **Core:** `LIQUIDITY_SWEEP_REVERSAL`, `TREND_PULLBACK_EMA`, `VOLUME_SURGE_BREAKOUT`, `BREAKDOWN_SHORT`, `SR_FLIP_RETEST`, `CONTINUATION_LIQUIDITY_SWEEP`, `POST_DISPLACEMENT_CONTINUATION`
- **Support:** `LIQUIDATION_REVERSAL`, `DIVERGENCE_CONTINUATION`, `OPENING_RANGE_BREAKOUT`, `FAILED_AUCTION_RECLAIM`
- **Specialist:** `WHALE_MOMENTUM`, `FUNDING_EXTREME_SIGNAL`, `QUIET_COMPRESSION_BREAK`

Source: `src/signal_quality.py:75-106`.

#### Actual evaluator-emitted setup strings

**Primary `360_SCALP` channel** (`src/channels/scalp.py`):
- `LIQUIDITY_SWEEP_REVERSAL` (`_evaluate_standard`, `src/channels/scalp.py:360-574`)
- `TREND_PULLBACK_EMA` (`_evaluate_trend_pullback`, `src/channels/scalp.py:609-750`)
- `LIQUIDATION_REVERSAL` (`src/channels/scalp.py:772-901`)
- `WHALE_MOMENTUM` (`src/channels/scalp.py:945-1097`)
- `VOLUME_SURGE_BREAKOUT` (`src/channels/scalp.py:1147-1322`)
- `BREAKDOWN_SHORT` (`src/channels/scalp.py:1363-1543`)
- `OPENING_RANGE_BREAKOUT` (`src/channels/scalp.py:1585-1715`)
- `SR_FLIP_RETEST` (`src/channels/scalp.py:1736-1974`)
- `FUNDING_EXTREME_SIGNAL` (`src/channels/scalp.py:2013-2148`)
- `QUIET_COMPRESSION_BREAK` (`src/channels/scalp.py:2169-2300`)
- `DIVERGENCE_CONTINUATION` (`src/channels/scalp.py:2321-2510`)
- `CONTINUATION_LIQUIDITY_SWEEP` (`src/channels/scalp.py:2534-2761`)
- `POST_DISPLACEMENT_CONTINUATION` (`src/channels/scalp.py:2791-3085`)
- `FAILED_AUCTION_RECLAIM` (`src/channels/scalp.py:3124-3389`)

**Auxiliary scalp-family channels**:
- `360_SCALP_FVG` → `FVG_RETEST`, sometimes upgraded to `FVG_RETEST_HTF_CONFLUENCE` (`src/channels/scalp_fvg.py:211-240`)
- `360_SCALP_DIVERGENCE` → `RSI_MACD_DIVERGENCE` (`src/channels/scalp_divergence.py:222-242`)
- `360_SCALP_ORDERBLOCK` → `SMC_ORDERBLOCK` (`src/channels/scalp_orderblock.py:252-274`)
- `360_SCALP_CVD` → `CVD_DIVERGENCE` (`src/channels/scalp_cvd.py:160-181`)
- `360_SCALP_VWAP` → `VWAP_BOUNCE` (`src/channels/scalp_vwap.py:173-197`)
- `360_SCALP_SUPERTREND` → `SUPERTREND_FLIP` (`src/channels/scalp_supertrend.py:170-190`)
- `360_SCALP_ICHIMOKU` → `ICHIMOKU_TK_CROSS` (`src/channels/scalp_ichimoku.py:186-206`)

#### Channel family inventory
- `360_SCALP`
- `360_SCALP_FVG`
- `360_SCALP_CVD`
- `360_SCALP_VWAP`
- `360_SCALP_DIVERGENCE`
- `360_SCALP_SUPERTREND`
- `360_SCALP_ICHIMOKU`
- `360_SCALP_ORDERBLOCK`

Source: `config/__init__.py:569-710`, `src/scanner/__init__.py:173-194`.

#### Production enablement status
Current defaults:
- **Enabled:** `360_SCALP`
- **Disabled by default:** `360_SCALP_FVG`, `360_SCALP_ORDERBLOCK`, `360_SCALP_DIVERGENCE`, `360_SCALP_CVD`, `360_SCALP_VWAP`, `360_SCALP_SUPERTREND`, `360_SCALP_ICHIMOKU`, and `OPENING_RANGE_BREAKOUT` logic inside `360_SCALP`

Source: `config/__init__.py:718-735`.

#### Persistence-facing path keys
`SignalRecord` persists raw `setup_class` strings, not display labels (`src/performance_tracker.py:28-55`, `src/performance_tracker.py:122-149`).
That means persisted history is keyed by internal `setup_class` names such as `SR_FLIP_RETEST`, `TREND_PULLBACK_EMA`, etc.

#### Naming-drift / observability-mismatch inventory
There is real naming drift:
- `SetupClass` knows `RSI_MACD_DIVERGENCE` and `SMC_ORDERBLOCK`, but `SIGNAL_TYPE_LABELS` still contains older-style names such as `DIVERGENCE_REVERSAL` and `ORDERBLOCK_BOUNCE` (`config/__init__.py:742-764`).
- Some evaluator-emitted strings are **not** in `SetupClass` at all: `CVD_DIVERGENCE`, `VWAP_BOUNCE`, `SUPERTREND_FLIP`, `ICHIMOKU_TK_CROSS` (`src/channels/scalp_cvd.py:160-181`, `src/channels/scalp_vwap.py:173-197`, `src/channels/scalp_supertrend.py:170-190`, `src/channels/scalp_ichimoku.py:186-206`).
- Because persistence stores raw `setup_class`, any monitor that expects display labels instead of stored keys can undercount or mis-group paths.

### Realistic operational inference
- The **effective production path family** is currently much closer to “`360_SCALP` plus optional radar candidates from disabled channels” than to the full code inventory.
- `CVD_DIVERGENCE`, `VWAP_BOUNCE`, `SUPERTREND_FLIP`, and `ICHIMOKU_TK_CROSS` look more like partially integrated or legacy naming families than fully normalized production persistence families.
- `MULTI_STRATEGY_CONFLUENCE` is a real emitted persistence label, but when it fires it overwrites the original winning path identity, reducing downstream path attribution fidelity (`src/scanner/__init__.py:3201-3239`).

---

## 2. End-to-end lifecycle map

### Confirmed code facts

1. **Symbol scan context built**
   - `_build_scan_context()` computes candles, indicators, SMC data, regime, pair quality, regime context, and order-flow metadata (`src/scanner/__init__.py:1507-1660`).

2. **Per-channel pre-scan skips**
   - `_should_skip_channel()` can reject before evaluator logic for tier gating, pair quality, volatile-unsuitable regime, paused channel, cooldown, symbol circuit breaker, already-active same channel, ranging-low-ADX, and regime/channel incompatibility (`src/scanner/__init__.py:1662-1790`).

3. **Detection / candidate creation**
   - `ScalpChannel.evaluate()` runs all 14 internal evaluators and returns every non-`None` candidate (`src/channels/scalp.py:317-354`).
   - All channels use `build_channel_signal()` to build a `Signal` with `signal_id`, entry, SL, TP, trailing defaults, entry zone, validity window, and `setup_class` (`src/channels/base.py:359-558`).

4. **Setup / execution / risk classification**
   - `_prepare_signal()` calls:
     - `classify_setup()` (`src/scanner/__init__.py:2120-2123`, `src/signal_quality.py:685-775`)
     - `execution_quality_check()` (`src/scanner/__init__.py:2125-2128`, `src/signal_quality.py:778-914`)
     - `build_risk_plan()` (`src/scanner/__init__.py:2414-2418`, `src/signal_quality.py:916-1285`)

5. **Scanner scoring / gating**
   - Hard gates / vetoes: failed-detection cooldown, setup incompatibility, execution failure, MTF hard gate, cross-asset hard gate, risk rejection, correlated exposure cap, OI invalidation, score below 50, stat filter, pair-analysis critical, SMC hard gate, trend hard gate, quiet-regime confidence floor, final min-confidence/component floor (`src/scanner/__init__.py:2085-2968`).
   - Soft penalties / modifiers: VWAP, kill zone, OI, funding, spoof, volume divergence, cluster, chart patterns, candlestick patterns, MTF boost/misalignment, regime transition, pair-analysis weak penalty (`src/scanner/__init__.py:2206-2815`).
   - Tiering: `A+` >= 80, `B` >= 65, `WATCHLIST` >= 50, else `FILTERED` (`src/scanner/__init__.py:383-402`, `src/scanner/__init__.py:2693-2745`).

6. **Same-direction arbitration inside `360_SCALP`**
   - Only the best-confidence candidate per symbol+direction survives (`src/scanner/__init__.py:3064-3117`).
   - Log strings: `Scalp arbitration: ... replaces ...` / `suppressed; ... retained`.

7. **Multi-strategy confluence rewriting**
   - If multiple channels align, the highest-confidence candidate can be rewritten to `MULTI_STRATEGY_CONFLUENCE` and boosted (`src/scanner/__init__.py:3201-3239`).

8. **Queueing / routing**
   - `_enqueue_signal()` pushes to `SignalQueue` (`src/scanner/__init__.py:2069-2070`).
   - `SignalRouter._process()` applies watchlist routing, position lock, cooldown, per-channel cap, correlation limit, TP/SL sanity, stale gate, AI enrichment, min-confidence, risk manager, Telegram delivery, and then registers `_active_signals` only after confirmed delivery (`src/signal_router.py:482-769`).

9. **Watchlist preview path**
   - Current code: `360_SCALP` `WATCHLIST` routes to `_route_watchlist_to_free()` and never enters `_active_signals` (`src/signal_router.py:482-489`, `src/signal_router.py:896-955`).
   - Message formatting is lightweight and intentionally omits entry/SL/TP (`src/telegram_bot.py:311-313`, `src/telegram_bot.py:514-531`).

10. **Radar / watch path for disabled channels**
    - Disabled channels are still evaluated in a radar pass; high-confidence candidates become free-channel radar watches, not paid signals (`src/scanner/__init__.py:3136-3195`, `src/main.py:403-445`, `src/free_watch_service.py:71-339`).

11. **Lifecycle tracking**
    - `TradeMonitor` polls active signals, updates PnL/MFE/MAE, handles DCA, SL, invalidation, TP1/TP2/TP3, expiry, and posts lifecycle updates (`src/trade_monitor.py:541-760`).

12. **Persistence**
    - Only terminal outcomes call `_record_outcome()`, which writes to `PerformanceTracker.record_outcome()` (`src/trade_monitor.py:219-328`, `src/trade_monitor.py:552-559`, `src/trade_monitor.py:634-693`).
    - `PerformanceTracker` appends `SignalRecord` and writes JSON to `data/signal_performance.json` (`src/performance_tracker.py:92-151`, `src/performance_tracker.py:1000-1039`, `config/__init__.py:904-905`).

### Realistic operational inference
- The true production funnel is much more selective than a plain “evaluator exists” reading suggests.
- The most operationally meaningful boundary is **not detection**; it is the set of transitions:
  1. evaluator emitted,
  2. `_prepare_signal()` survived,
  3. arbitration winner,
  4. router accepted and posted,
  5. monitor produced a terminal outcome.
- Anything before step 5 is upstream activity, not proof of real expression.

---

## 3. Drop-off / suppression map

### Confirmed code facts

#### Before a candidate exists
- Channel disabled by default (`config/__init__.py:718-735`)
- `_should_skip_channel()` pre-filter:
  - Tier-2 pair excluded from `360_SCALP` (`src/scanner/__init__.py:1663-1669`)
  - Pair quality fail (`src/scanner/__init__.py:1670-1723`)
  - Volatile unsuitable for non-primary channels (`src/scanner/__init__.py:1724-1737`)
  - Paused channel (`src/scanner/__init__.py:1738-1740`)
  - Per-symbol/channel cooldown (`src/scanner/__init__.py:1741-1744`)
  - Per-symbol circuit breaker (`src/scanner/__init__.py:1745-1752`)
  - Same symbol/channel already active (`src/scanner/__init__.py:1753-1759`)
  - Ranging + low ADX suppression for `360_SCALP` (`src/scanner/__init__.py:1760-1771`)
  - Regime/channel incompatibility (`src/scanner/__init__.py:1772-1789`)

#### Candidate exists but dies in `_prepare_signal()`
- Failed-detection cooldown (`src/scanner/__init__.py:2085-2094`)
- Evaluator exception / `None` (`src/scanner/__init__.py:2101-2115`)
- Setup incompatibility (`src/scanner/__init__.py:2120-2123`)
- Execution quality fail (`src/scanner/__init__.py:2125-2128`)
- MTF hard gate (`src/scanner/__init__.py:2147-2196`)
- Cross-asset hard gate (`src/scanner/__init__.py:2316-2337`)
- Risk-plan rejection (`src/scanner/__init__.py:2414-2418`, `src/signal_quality.py:982-1070`)
- Correlated exposure cap (`src/scanner/__init__.py:2420-2435`)
- OI invalidation in base confidence (`src/scanner/__init__.py:1890-1896`)
- Composite score < 50 (`src/scanner/__init__.py:2693-2717`)
- Stat filter suppression (`src/scanner/__init__.py:2747-2774`)
- Pair-analysis critical suppression / weak penalty (`src/scanner/__init__.py:2776-2815`)
- SMC hard gate (`src/scanner/__init__.py:2817-2852`)
- Trend hard gate (`src/scanner/__init__.py:2854-2881`)
- Quiet scalp floor / failed-detection cooldown trigger (`src/scanner/__init__.py:2901-2941`)
- Final confidence / component floor (`src/scanner/__init__.py:2955-2968`)

#### Candidate survives `_prepare_signal()` but still dies before persistence
- Lost in same-direction arbitration (`src/scanner/__init__.py:3064-3117`)
- Rewritten under `MULTI_STRATEGY_CONFLUENCE`, masking original path identity (`src/scanner/__init__.py:3201-3239`)
- Queue accepted but router blocks for:
  - existing position lock (`src/signal_router.py:491-499`)
  - cooldown (`src/signal_router.py:501-513`)
  - per-channel cap (`src/signal_router.py:515-526`)
  - correlation limit (`src/signal_router.py:528-543`)
  - TP/SL sanity (`src/signal_router.py:545-571`)
  - stale time / stale price (`src/signal_router.py:573-627`)
  - min-confidence (`src/signal_router.py:632-642`)
  - risk-manager block (`src/signal_router.py:644-655`)
  - delivery failure after retries (`src/signal_router.py:676-716`)
- `WATCHLIST` free preview only, so no lifecycle/persistence (`src/signal_router.py:482-489`, `src/signal_router.py:896-955`)
- Radar watch only, so no lifecycle/persistence (`src/scanner/__init__.py:3136-3195`, `src/free_watch_service.py:71-339`)
- Routed signal remains active but never reaches a terminal outcome yet, so no `signal_performance.json` row yet (`src/trade_monitor.py:219-328`)

#### Persistence blind spots / attribution blind spots
- Persistence is terminal-event only; no row for “candidate reached scoring” or “signal routed” (`src/performance_tracker.py:92-151`).
- `MULTI_STRATEGY_CONFLUENCE` overwrites the winning signal’s original `setup_class`, so original path ancestry is lost in persisted history (`src/scanner/__init__.py:3213-3224`).
- Auxiliary disabled-channel radar candidates are observable in free-watch state, but not in `signal_performance.json` (`src/free_watch_service.py:71-339`).

### Realistic operational inference
- The heaviest practical suppressors look like:
  1. **channel disablement**,
  2. **pair quality / spread**,
  3. **MTF gate**,
  4. **per-direction arbitration**,
  5. **router non-persistence paths** (`WATCHLIST`, radar),
  6. **terminal-only persistence**.
- The fetched live monitor supports that reading: recent suppressor output is dominated by pair-quality spread, `mtf_gate:360_SCALP`, and volatile-unsuitable counts for disabled auxiliary channels (`origin/monitor-logs:monitor/latest.txt:56-69`).

---

## 4. Realistic operational interpretation

### Confirmed code facts
- Only `360_SCALP` is enabled by default (`config/__init__.py:718-735`).
- Auxiliary channels still get evaluated in radar mode when disabled, but that path creates free-channel watches, not paid signals or performance records (`src/scanner/__init__.py:3136-3195`, `src/main.py:403-445`).
- Current router code segregates `WATCHLIST` into a free preview path (`src/signal_router.py:482-489`, `src/signal_router.py:896-955`).
- The live monitor snapshot still shows a history file dominated by sub-65 `TREND_PULLBACK_EMA` and `SR_FLIP_RETEST` outcomes, with four `CONTINUATION_LIQUIDITY_SWEEP` and one recent `LIQUIDITY_SWEEP_REVERSAL` (`origin/monitor-logs:monitor/latest.txt:75-127`).

### Realistic operational inference
- **Most likely live reality:** the engine is currently expressing mainly a handful of main-channel families because the code is intentionally running a very narrow active portfolio. The rest of the codebase is mostly latent inventory, disabled inventory, radar inventory, or non-normalized inventory.
- **Most likely explanation for the low-confidence persisted history still visible in the monitor:** those records were probably created under an earlier runtime state before the current watchlist segregation logic, and they remain in `signal_performance.json` because persistence is append-only history. The current snapshot itself supports this interpretation because the latest new record is an `83.0` `LIQUIDITY_SWEEP_REVERSAL`, while the scanner telemetry now shows `WATCHLIST` candidates and suppressor counters without proving they were routed into persistence (`origin/monitor-logs:monitor/latest.txt:56-69`, `origin/monitor-logs:monitor/latest.txt:82-127`).
- **Which families seem implemented but under-expressing?**
  - `VOLUME_SURGE_BREAKOUT`, `BREAKDOWN_SHORT`, `FUNDING_EXTREME_SIGNAL`, `QUIET_COMPRESSION_BREAK`, `FAILED_AUCTION_RECLAIM`, and `DIVERGENCE_CONTINUATION` look production-designed in `360_SCALP` but are likely under-expressing because they require tighter structural preconditions than the live dominant trio.
  - `FVG_RETEST`, `SMC_ORDERBLOCK`, `RSI_MACD_DIVERGENCE` are better integrated than the other auxiliary-channel families, but still under-express operationally because their channels are disabled by default.
  - `CVD_DIVERGENCE`, `VWAP_BOUNCE`, `SUPERTREND_FLIP`, and `ICHIMOKU_TK_CROSS` look implemented upstream but not fully normalized as production persistence families.
- **Likely dominant bottlenecks:** pair quality / spread, MTF gate, same-direction arbitration, and the fact that only terminal outcomes persist.
- **Likely practical outcome:** narrow live diversity is mostly genuine selectivity plus disabled-channel policy, with some historical persistence contamination and some naming blindness layered on top.

---

## 5. Why persisted history currently shows only a subset of paths

### Confirmed code facts
1. `signal_performance.json` persists only terminal outcomes (`src/trade_monitor.py:219-328`, `src/performance_tracker.py:92-151`).
2. `WATCHLIST` no longer enters the paid lifecycle in current code (`src/signal_router.py:482-489`).
3. Disabled channels still create radar/watch activity, not persisted trade records (`src/scanner/__init__.py:3136-3195`).
4. The fetched monitor snapshot’s persisted history currently contains only:
   - `TREND_PULLBACK_EMA`
   - `SR_FLIP_RETEST`
   - `CONTINUATION_LIQUIDITY_SWEEP`
   - `LIQUIDITY_SWEEP_REVERSAL`

   Source: `origin/monitor-logs:monitor/latest.txt:121-127`.

### Realistic operational inference
The narrow subset is most plausibly caused by **a combination** of:
- **genuine active-portfolio narrowing**: only `360_SCALP` is enabled by default,
- **heavy upstream suppression**: many candidates never survive to routing,
- **router/persistence gating**: watchlist and radar activity are intentionally non-persisted,
- **historical contamination**: old low-confidence records still sit in the same history file,
- **naming drift**: some families would be hard to aggregate consistently even if they did fire,
- **terminal-only persistence**: a path can be very active upstream and still invisible in `signal_performance.json` if it rarely becomes a routed, closed trade.

What it is **least** likely to be:
- a pure logging bug,
- or proof that most implemented paths are live and healthy but just hidden.

The dominant operational story is closer to **selective production expression + persistence scope limits + some legacy history**.

---

## 6. Best instrumentation points for a future path-expression monitor section

| Hook | What it can prove | File/component | Data source | Reliability | Notes |
|---|---|---|---|---|---|
| `candidate_reached_scoring:<setup>` counters | A path reached post-gate scoring | `src/scanner/__init__.py:2628-2632` | log-based counter | High for upstream activity | Not proof of routing or persistence |
| `score_80plus/65to79/50to64:<setup>` counters | Final score-band distribution per path | `src/scanner/__init__.py:2694-2705` | log-based counter | High for scoring-stage visibility | Best upstream path-funnel view |
| `Scan cycle suppression summary` | Which suppressors dominate current live flow | `src/scanner/__init__.py:1071-1088`; seen in `origin/monitor-logs:monitor/latest.txt:56-69` | log-based | High for short-window operations | Good for explaining why paths die |
| `Scalp arbitration: ... suppressed/retained` | Which same-direction paths lost to stronger siblings | `src/scanner/__init__.py:3094-3112` | log-based | High | Critical for hidden path competition |
| `Signal diversity (last 100 cycles)` | Evaluated vs emitted setup diversity | `src/scanner/__init__.py:1173-1182` | log-based | High | Best path breadth summary when present |
| `_route_watchlist_to_free()` / watchlist preview log | Path reached preview-only expression | `src/signal_router.py:896-917` | log-based | High | Proof of non-persisted expression |
| Radar watch creation / resolution | Disabled-channel candidate expression | `src/main.py:403-445`, `src/free_watch_service.py:141-339` | log + Redis state | Medium-high | Useful for “candidate but not paid” inventory |
| `Signal posted → channel | symbol dir` | Real routed paid expression | `src/signal_router.py:717-722` | log-based | High | Best proof a path became live |
| `_active_signals` registration | Signal entered lifecycle tracking | `src/signal_router.py:740-744` | in-memory/Redis state | High | Better than raw post logs if accessible |
| TradeMonitor terminal events (`SL_HIT`, `INVALIDATED`, `FULL TP HIT`, `EXPIRED`) | Path reached a terminal lifecycle event | `src/trade_monitor.py:552-559`, `src/trade_monitor.py:634-693` | log-based | High | Precedes persistence write |
| `PerformanceTracker.record_outcome()` / loaded stats | Path persisted into historical outcomes | `src/trade_monitor.py:252-276`, `src/performance_tracker.py:92-151` | persisted-data-based | Very high | Ground truth for closed trades only |
| `get_stats_by_method(setup_name)` | Post-hoc persisted path-level performance | `src/performance_tracker.py:901-923` | persisted-data-based | Very high | Best long-window outcome metric |

### Recommended monitor layout
1. **Upstream candidate expression**: `candidate_reached_scoring`, score-band counters, diversity counters.
2. **Suppression layer**: suppression summary + top suppressor keys.
3. **Real routed expression**: posted signals + `_active_signals` counts by `setup_class`.
4. **Non-persisted expression**: watchlist previews + radar watch creation/resolution.
5. **Persisted outcome layer**: `signal_performance.json` by-path summary.

That separates “candidate activity” from “real production expression” instead of mixing them.

---

## 7. Most important findings / recommendations

### Most important findings
1. **The codebase path inventory is much larger than the effective production path inventory.** The default live portfolio is heavily concentrated in `360_SCALP`.
2. **Persistence is terminal-event only.** A path can be active upstream and still be absent from `signal_performance.json`.
3. **Current code truth and live monitor history are not perfectly aligned.** Current code segregates `WATCHLIST`, but the fetched history still contains many sub-65 records, strongly suggesting historical persistence contamination or runtime lag.
4. **Auxiliary channels are not the best explanation for current persisted diversity.** Most are disabled by default and/or only visible through radar/watch hooks.
5. **Naming drift is real.** Some auxiliary families use setup strings that are not canonical `SetupClass` values, which creates observability and future persistence-normalization risk.

### Recommendations
1. **Treat current repository code as the authoritative routing truth, and older checked-in audit docs as historical context only.**
2. **Build the future “Path Expression Audit” around multiple funnel stages, not just `signal_performance.json`.**
3. **Add explicit path-level metrics for:**
   - reached scoring,
   - score band,
   - arbitration losses,
   - routed paid signals,
   - watchlist previews,
   - radar watch creation/resolution,
   - terminal outcomes,
   - persisted records.
4. **Normalize auxiliary path naming before expecting robust path-level analytics** for `CVD_DIVERGENCE`, `VWAP_BOUNCE`, `SUPERTREND_FLIP`, and `ICHIMOKU_TK_CROSS`.
5. **When interpreting the current persisted history, assume it is a lagging and partially contaminated lens, not a full picture of present-day path expression.**
