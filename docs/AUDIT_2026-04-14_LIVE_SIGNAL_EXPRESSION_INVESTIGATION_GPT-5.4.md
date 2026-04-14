# Live 360_SCALP Signal Expression Investigation

- Date: 2026-04-14
- Repository: `mkmk749278/360-v2`
- Branch investigated: `main`
- Model used: `GPT-5.4`
- Scope statement: Investigate current live `360_SCALP` signal-expression quality, lifecycle correctness, and routing/governance integrity using repository code plus the latest live monitor evidence from `refs/heads/monitor-logs:monitor/latest.txt` (generated 2026-04-14 05:33:29 UTC).

## 1. Executive summary

The biggest confirmed issue is **not evaluator silence anymore; it is governance/lifecycle leakage**.

- **WATCHLIST is not just a preview in current runtime.** In current code, `360_SCALP` WATCHLIST candidates (`50–64`) are still dispatched through the main paid router path, added to `SignalRouter._active_signals`, and then monitored by `TradeMonitor` exactly like real live trades (`src/scanner/__init__.py:2942-2953`, `src/signal_router.py:628-647`, `src/signal_router.py:745-756`, `src/trade_monitor.py:367-403`).
- The latest live monitor proves that low-confidence setups are becoming real tracked outcomes: the last 10 live signals include multiple `TREND_PULLBACK_EMA`, `SR_FLIP_RETEST`, and one `CONTINUATION_LIQUIDITY_SWEEP`, all with confidence `55.0–61.3`, and nearly all ended `SL_HIT`/`CLOSED` (`refs/heads/monitor-logs:monitor/latest.txt:64-76`).
- **This directly contradicts doctrine.** `OWNER_BRIEF.md` says `WATCHLIST` = `50–64` = “Post to free channel only” (`OWNER_BRIEF.md:467-474`). Current code instead routes WATCHLIST through the paid signal object and lifecycle machinery.
- **Duplicate lifecycle posting has two different truths:**
  1. **Confirmed message duplication by design** for stop-style exits: `_evaluate_signal()` posts `_post_update(...)` and then `_post_signal_closed(..., is_tp=False)` to the same active channel for the same terminal event (`src/trade_monitor.py:632-650`, `src/trade_monitor.py:931-1010`). This is the most likely cause of duplicate “SL / stopped out” style output.
  2. **Confirmed missing idempotency guard**: there is no sent-event registry in `TradeMonitor`; `_post_update()` and `_post_signal_closed()` blindly send every time they are called (`src/trade_monitor.py:931-1010`).
- **Current live quality concentration is real, but unevenly evidenced.**
  - `TREND_PULLBACK_EMA` is dominant in recent resolved live history: 6 of the last 10 recorded signals (`refs/heads/monitor-logs:monitor/latest.txt:64-76`).
  - `SR_FLIP_RETEST` is dominant in the current scoring funnel: 26 reached scoring in the last 100 cycles, with 15 B-tier, 6 WATCHLIST, 1 A+ (`refs/heads/monitor-logs:monitor/latest.txt:215-216`).
  - `CONTINUATION_LIQUIDITY_SWEEP` appears in recent live losses, but the latest checked-in funnel telemetry does **not** show it as a current dominant scorer (`refs/heads/monitor-logs:monitor/latest.txt:64-76`, `215-216`).

**Best next action:** fix WATCHLIST lifecycle admission first. Until WATCHLIST is separated from paid/live lifecycle, current live-quality evidence is contaminated by low-confidence preview objects being treated as real trades.

## 2. What is confirmed vs unconfirmed

### Confirmed

- `classify_signal_tier()` defines `A+ = 80+`, `B = 65–79`, `WATCHLIST = 50–64` (`src/scanner/__init__.py:383-402`).
- Scanner preserves WATCHLIST candidates instead of rejecting them (`src/scanner/__init__.py:2942-2953`).
- Router explicitly bypasses the channel min-confidence floor for `360_SCALP` WATCHLIST (`src/signal_router.py:628-647`).
- Router then posts the signal and registers it as active regardless of tier (`src/signal_router.py:663-756`).
- Trade monitor polls **all** active signals, updates price, and can auto-execute them if execution is enabled; it has no WATCHLIST exclusion (`src/trade_monitor.py:367-403`).
- Router pulse loop already treats WATCHLIST as “pre-confirmation” and skips live-status pulses (`src/signal_router.py:354-362`), so the codebase itself already partially acknowledges WATCHLIST is not a true live trade.
- Recent live history shows sub-65 `TREND_PULLBACK_EMA`, `SR_FLIP_RETEST`, and `CONTINUATION_LIQUIDITY_SWEEP` signals being tracked to terminal outcomes (`refs/heads/monitor-logs:monitor/latest.txt:64-76`).
- Duplicate SL-style output is structurally possible by design because final stop outcomes call two posting functions to the same channel (`src/trade_monitor.py:632-650`, `src/trade_monitor.py:931-1010`).
- No lifecycle idempotency guard exists for invalidation/SL/TP/expiry posts (`src/trade_monitor.py:931-1010`).

### Unconfirmed

- The exact production trigger of the reported **duplicate INVALIDATED** post is not proven from checked-in monitor evidence. Code review shows only one explicit invalidation branch, so the production duplicate likely comes from generic missing idempotency, transport retry duplication, or re-entry via broader lifecycle reuse; code alone cannot isolate which one fired.
- Current live overrepresentation of `CONTINUATION_LIQUIDITY_SWEEP` is not proven by the latest funnel telemetry snapshot. It is present in recent losing history, but not dominant in the last-100-cycle scoring counters.
- The currently active live signal seen in the monitor (`active_signal:360_SCALP = 1`) cannot be conclusively identified as WATCHLIST vs B/A from checked-in evidence alone.

## 3. WATCHLIST lifecycle truth

### End-to-end trace

1. `ScalpChannel.evaluate()` runs all 14 internal evaluators and returns every non-`None` candidate (`src/channels/scalp.py:317-354`).
2. `Scanner._scan_symbol()` sends each `360_SCALP` candidate through `_prepare_signal()` and keeps the best candidate per direction (`src/scanner/__init__.py:3038-3116`).
3. `_prepare_signal()` computes the final score/tier. If the final tier is `WATCHLIST` and the channel is in `_SCALP_CHANNELS`, it returns the signal instead of rejecting it (`src/scanner/__init__.py:2693-2745`, `src/scanner/__init__.py:2942-2953`).
4. The comment says WATCHLIST should “clear entry/SL/TP for zone-alert-only format”, but the code does **not** clear those fields before returning (`src/scanner/__init__.py:2951-2953`). The `Signal` still carries full executable trade geometry.
5. The signal is enqueued and consumed by `SignalRouter._process()` (`src/scanner/__init__.py:3240-3254`, `src/signal_router.py:482-647`).
6. Router explicitly bypasses the normal `min_confidence` floor for `360_SCALP` WATCHLIST (`src/signal_router.py:628-647`).
7. Router formats and posts the signal to the main configured channel via `CHANNEL_TELEGRAM_MAP`, then stores it in `_active_signals` (`src/signal_router.py:663-756`).
8. `TelegramBot.format_signal()` only changes the initial message format for WATCHLIST; it does **not** change lifecycle admission (`src/telegram_bot.py:291-313`, `src/telegram_bot.py:514-531`).
9. `TradeMonitor._check_all()` then price-updates and evaluates every active signal, including potential order execution when enabled (`src/trade_monitor.py:367-403`).

### Direct answers

- **Is WATCHLIST just an informational preview?**  
  **Doctrine says yes; runtime says no.**
- **Can WATCHLIST candidates become full active/tracked signals?**  
  **Yes.**
- **Where does that happen?**  
  Scanner preserves them in `_prepare_signal()`; router bypasses the floor and registers them in `_active_signals`; trade monitor then manages them (`src/scanner/__init__.py:2942-2953`, `src/signal_router.py:628-647`, `src/signal_router.py:745-756`, `src/trade_monitor.py:367-403`).
- **Under what conditions?**  
  Final tier = `WATCHLIST`, channel in `_SCALP_CHANNELS`, and for actual downstream dispatch the channel is `360_SCALP` so the router bypass applies.
- **Is that behavior correct under current doctrine?**  
  **No.** `OWNER_BRIEF.md` says WATCHLIST should be “Post to free channel only” (`OWNER_BRIEF.md:467-474`). Current code converts WATCHLIST into a paid-channel `Signal` object with trade-monitor lifecycle.

### Strongest live proof

The latest VPS monitor shows low-confidence signals already resolved as real tracked trades:

- 6 `TREND_PULLBACK_EMA` at `55.0–60.2`, mostly `SL_HIT`
- 3 `SR_FLIP_RETEST` at `58.3–61.3`, `SL_HIT/CLOSED`
- 1 `CONTINUATION_LIQUIDITY_SWEEP` at `56.0`, `SL_HIT`

(`refs/heads/monitor-logs:monitor/latest.txt:64-76`)

That is only possible because those objects entered the real active-signal lifecycle.

## 4. Duplicate posting root cause

### Posting paths

- Invalidation update: `_evaluate_signal()` → `_post_update(sig, "🔄 INVALIDATED (...)")` (`src/trade_monitor.py:657-672`)
- Stop-loss / breakeven / profit-locked update: `_evaluate_signal()` → `_post_update(sig, outcome_event)` (`src/trade_monitor.py:632-650`)
- TP1 / TP2 updates: `_evaluate_signal()` → `_post_update(sig, "... TP1/TP2 ...")` (`src/trade_monitor.py:696-775`)
- Full TP close: `_evaluate_signal()` → `_post_update("FULL TP HIT")` + `_post_signal_closed(..., is_tp=True)` (`src/trade_monitor.py:677-695`, `737-754`)
- Stop-style close summary: `_evaluate_signal()` → `_post_update(outcome_event)` + `_post_signal_closed(..., is_tp=False)` (`src/trade_monitor.py:632-650`)
- Expiry update in monitor: `_evaluate_signal()` → `_post_update("⏰ EXPIRED ...")` (`src/trade_monitor.py:552-560`)
- Expiry update in router: `cleanup_expired()` → `_notify_signal_expiry()` (`src/signal_router.py:1081-1146`)

### Idempotency reality

- There is **no** sent-event registry, message fingerprint cache, or `(signal_id, event_kind)` guard in `TradeMonitor`.
- `_post_update()` and `_post_signal_closed()` simply build text and send it (`src/trade_monitor.py:931-1010`).
- Telegram send retries also have no request-level idempotency key (`src/telegram_bot.py:48-120`).

### Most likely root causes

#### A. Confirmed: duplicate SL-style output is built in

For stop-style terminal outcomes, the monitor intentionally sends:

1. an explicit lifecycle update (`🔴 SL HIT`, `⚪ BREAKEVEN EXIT`, or `🟢 PROFIT LOCKED`)
2. then a second active-channel “signal closed” summary that is also stop-themed (`formatter.format_signal_closed_sl()` renders `🛑 ... stopped out` / `Stopped at ...`)

(`src/trade_monitor.py:632-650`, `src/formatter.py:310-344`)

That is not a race; it is current design.

#### B. Confirmed: no generic idempotency guard exists

If the same lifecycle branch is reached twice, nothing stops the second post. This makes duplicates possible from any future re-entry condition.

#### C. Confirmed: expiry has split ownership

Expiry can be emitted by both `TradeMonitor._evaluate_signal()` and `SignalRouter.cleanup_expired()`. Because the monitor evaluates a snapshot copy of active signals, router-side removal does not prevent the monitor from still processing the same object in that poll cycle. That creates a real duplicate-expiry risk (`src/trade_monitor.py:367-403`, `552-560`; `src/signal_router.py:1109-1146`).

#### D. Unconfirmed but plausible for duplicate INVALIDATED

The code has only one explicit invalidation-post branch. So production duplicate `INVALIDATED` messages are most plausibly explained by:

- generic lack of lifecycle idempotency,
- transport retry duplication, or
- the same signal object being re-processed after wider state/lifecycle reuse.

Code review does **not** prove a second explicit invalidation-post path.

### Smallest correct fix

1. **Stop dual-posting stop-style terminal events.** Keep the explicit `_post_update()` for `SL_HIT` / `BREAKEVEN_EXIT` / `PROFIT_LOCKED`; do not also send `_post_signal_closed(..., is_tp=False)`.
2. **Add a per-signal lifecycle-send guard** inside `TradeMonitor`, keyed at minimum by `(signal_id, event_kind)`.
3. **Make expiry single-owner.** Prefer `TradeMonitor` as the posting owner and keep `SignalRouter.cleanup_expired()` as silent cleanup only, or vice versa.

## 5. Confidence/tier/routing truth

### Current semantics

- Tier classification: `A+ >= 80`, `B >= 65`, `WATCHLIST >= 50` (`src/scanner/__init__.py:383-402`)
- `CHANNEL_SCALP.min_confidence = 65` (`config/__init__.py:569-583`)
- Scanner WATCHLIST short-circuit applies to all scalp-family channels (`src/scanner/__init__.py:169-177`, `2942-2953`)
- Router WATCHLIST bypass applies only to `360_SCALP` (`src/signal_router.py:628-647`)
- Router free-channel publish is **not** the WATCHLIST route; it only posts condensed free previews when confidence `>= 75` (`src/signal_router.py:897-926`)

### Practical truth

- **A+ and B:** posted to paid channel and tracked as active signals.
- **WATCHLIST on `360_SCALP`:** also posted to paid channel and tracked as active signals.
- **WATCHLIST on auxiliary scalp channels:** scanner may preserve them, but router still rejects them because bypass is scoped to `360_SCALP`.

### Core mismatch

The repository currently has three different WATCHLIST meanings:

1. **Docs/doctrine:** free-only preview (`OWNER_BRIEF.md:467-474`)
2. **Router pulse logic:** pre-confirmation, not eligible for live-status pulses (`src/signal_router.py:354-362`)
3. **Trade lifecycle reality:** still a paid-channel active signal monitored like a trade (`src/signal_router.py:745-756`, `src/trade_monitor.py:367-403`)

That is the central routing/governance integrity failure.

## 6. Setup-family quality findings

## Live evidence first

- Recent resolved live history is heavily concentrated in **low-confidence `TREND_PULLBACK_EMA`** and **low-confidence `SR_FLIP_RETEST`**, with one recent **low-confidence `CONTINUATION_LIQUIDITY_SWEEP`**; almost all lost quickly (`refs/heads/monitor-logs:monitor/latest.txt:64-76`).
- Current last-100-cycle funnel telemetry shows:
  - `SR_FLIP_RETEST`: `26` reached scoring, `15` B-tier, `6` WATCHLIST, `1` A+.
  - `LIQUIDITY_SWEEP_REVERSAL`: `4` reached scoring, all `WATCHLIST`.
  - No corresponding dominant `TREND_PULLBACK_EMA` or `CONTINUATION_LIQUIDITY_SWEEP` scoring count appears in the same snapshot.
  (`refs/heads/monitor-logs:monitor/latest.txt:215-216`)

### What the code says

#### `TREND_PULLBACK_EMA`

- Hard gates are not especially loose: trending regime only, strict EMA stack, price near EMA9/21, RSI `40–60`, directional last candle, and at least one FVG/orderblock (`src/channels/scalp.py:619-684`).
- It is exempt from the SMC hard gate because sweep-based scoring does not fit this thesis (`src/scanner/__init__.py:232-259`).
- It has **no** path-specific soft-penalty model; after evaluator entry it mostly depends on shared scoring and downstream routing (`src/channels/scalp.py:731-764`).
- Conclusion: current live weak `TREND_PULLBACK_EMA` expression looks less like evaluator permissiveness and more like **WATCHLIST/tracking governance leakage**. The live losses are mostly `55–60` confidence, which should never have been treated as real trades under doctrine.

#### `SR_FLIP_RETEST`

- This path was deliberately softened in several places:
  - flip search window widened,
  - 0.3% retest gate expanded to 0.6% with only soft penalty,
  - wick quality softened,
  - RSI softened,
  - missing FVG/orderblock softened in fast regimes
  (`src/channels/scalp.py:1746-1775`, `1827-1905`, `1988-2004`).
- It is exempt from the SMC hard gate (`src/scanner/__init__.py:232-248`).
- Live funnel telemetry now shows it as the dominant current main-path scorer (`refs/heads/monitor-logs:monitor/latest.txt:215-216`).
- Conclusion: **SR_FLIP_RETEST is the strongest confirmed family-level quality concern.** This is not just routing leakage; the evaluator itself has been intentionally widened and is now producing many B/WATCHLIST candidates.

#### `CONTINUATION_LIQUIDITY_SWEEP`

- Hard gates remain stronger than the other two: valid regimes only, EMA trend, ADX floor, actual sweep in trend direction, reclaimed sweep level, momentum alignment (`src/channels/scalp.py:2544-2685`).
- Quality softening exists, but only around RSI, missing FVG/orderblock, and older sweep recency (`src/channels/scalp.py:2659-2685`, `2779-2783`).
- Latest checked-in live funnel telemetry does not show it as dominant, though recent history shows at least one weak loser (`refs/heads/monitor-logs:monitor/latest.txt:64-76`, `215-216`).
- Conclusion: **concern is plausible but not yet proven as a current primary contributor**.

### Telemetry hooks that already exist

- Per-cycle suppression counters and per-path scoring-tier counters (`src/scanner/__init__.py:1071-1191`, `2631-2716`)
- Setup evaluated/emitted diversity counters every 100 cycles (`src/scanner/__init__.py:1173-1182`, `3115-3247`)
- Outcome tracking by `setup_class` in `PerformanceTracker.record_outcome()` and `get_stats_by_method()` (`src/performance_tracker.py:92-157`, `901-923`)

### Bottom line on family quality

- **Confirmed current problem family:** `SR_FLIP_RETEST`
- **Confirmed recent-loss family:** `TREND_PULLBACK_EMA`
- **Present but not yet dominant by checked-in telemetry:** `CONTINUATION_LIQUIDITY_SWEEP`
- **Most important interpretation:** current low-quality live expression is a mix of **family-level quality issues** and **WATCHLIST lifecycle leakage**; do not tune families before fixing the governance leak.

## 7. Governance mismatches

1. **Docs vs runtime:**  
   `OWNER_BRIEF.md` says WATCHLIST is free-only (`OWNER_BRIEF.md:467-474`); runtime routes `360_SCALP` WATCHLIST through paid active-signal lifecycle.

2. **Docs vs monitor:**  
   `docs/ACTIVE_CONTEXT.md` says PR-18 aligned WATCHLIST handling downstream (`docs/ACTIVE_CONTEXT.md:42`, `48`, `69`). Current live history shows sub-65 signals still becoming tracked outcomes (`refs/heads/monitor-logs:monitor/latest.txt:64-76`).

3. **Code vs code:**  
   Router pulse loop treats WATCHLIST as pre-confirmation and “not eligible for live status” (`src/signal_router.py:354-362`), but trade monitor still treats the same object as a live trade (`src/trade_monitor.py:367-403`).

4. **Code vs code comment:**  
   Scanner comment says WATCHLIST should be zone-alert-only with entry/SL/TP cleared, but code returns the full `Signal` unchanged (`src/scanner/__init__.py:2951-2953`).

5. **Tests vs doctrine:**  
   PR-18 tests explicitly assert that a WATCHLIST `360_SCALP` signal is dispatched (`tests/test_pr18_scalp_tier_dispatch_alignment.py:194-207`), while doctrine says WATCHLIST is free-only and pulse logic says it is not live-status eligible.

## 8. Immediate bugs to fix now

1. **WATCHLIST active-lifecycle admission bug**  
   WATCHLIST should not enter `SignalRouter._active_signals`, `TradeMonitor`, or auto-execution.

2. **Stop-style duplicate posting bug**  
   Stop outcomes currently emit both `_post_update()` and `_post_signal_closed(..., is_tp=False)`.

3. **Missing lifecycle idempotency**  
   Add an event-send guard in `TradeMonitor`.

4. **Split expiry ownership**  
   Remove the dual posting path between `TradeMonitor` and `SignalRouter.cleanup_expired()`.

5. **Scanner WATCHLIST comment/implementation mismatch**  
   Either actually strip executable trade geometry for preview-only objects, or stop pretending the object is preview-only. Under doctrine, the correct answer is to stop admitting it to live lifecycle.

## 9. Best next PR recommendation

### Rank 1 — WATCHLIST lifecycle segregation (best next PR)

Why first:

- It fixes the biggest truth/integrity failure.
- It likely explains a large share of the current “weak live expression” problem.
- It prevents preview objects from being treated as live trades and, if execution is ever enabled, as executable orders.

Recommended scope:

- Route `360_SCALP` WATCHLIST to the free/watchlist path only.
- Do not register WATCHLIST in `SignalRouter._active_signals`.
- Add a defensive `TradeMonitor` guard that skips any WATCHLIST object.
- Align tests and docs to the real doctrine.

### Rank 2 — Lifecycle idempotency / duplicate-post PR

Why second:

- The user-visible duplication problem is real, but it is narrower than the governance leak.
- The smallest strong fix is localized to `TradeMonitor` and `SignalRouter.cleanup_expired()`.

Recommended scope:

- Remove stop-style double posting.
- Add `(signal_id, event_kind)` send guard.
- Centralize expiry posting ownership.

### Rank 3 — Evidence-based `SR_FLIP_RETEST` quality tightening PR

Why third:

- `SR_FLIP_RETEST` is the strongest confirmed family-level concern.
- But tuning it before fixing WATCHLIST admission would mix a governance fix with a quality-model change and make post-fix telemetry harder to interpret.

Recommended scope later:

- Revisit the widened retest/wick/RSI/SMC relaxations with live post-fix telemetry.

## 10. Deferred items that should NOT be changed yet

- Do **not** broadly loosen spread thresholds.
- Do **not** broadly lower quiet-regime floors.
- Do **not** broadly weaken the generic MTF gate yet; re-evaluate after WATCHLIST segregation, because current paid/live evidence is contaminated by WATCHLIST leakage.
- Do **not** broadly retune `TREND_PULLBACK_EMA` or `CONTINUATION_LIQUIDITY_SWEEP` yet; current checked-in evidence is weaker than for `SR_FLIP_RETEST`.
- Do **not** redesign the whole signal architecture. The smallest strong sequence is:
  1. fix WATCHLIST lifecycle truth,
  2. fix lifecycle idempotency/duplicate posting,
  3. then re-read live telemetry before any family tuning.
