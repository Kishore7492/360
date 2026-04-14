# AUDIT 2026-04-14 — Report Comparison and Canonical Verdict

- Title: Report Comparison and Canonical Verdict
- Date: 2026-04-14
- Repository: mkmk749278/360-v2
- Branch: main
- Canonical status: FINAL

## Final Canonical Verdict

The primary confirmed defect is **WATCHLIST lifecycle admission**.

`WATCHLIST` (`50–64`) is documented as **free-channel-only preview material**, but current `360_SCALP` runtime preserves it, bypasses the router min-confidence floor, posts it through the paid channel path, registers it in `_active_signals`, and lets `TradeMonitor` manage it like a real live trade (`src/scanner/__init__.py:2942-2953`, `src/signal_router.py:628-756`, `src/trade_monitor.py:367-403`, `OWNER_BRIEF.md:467-474`).

That mismatch is the best-supported explanation for low-confidence paid/live pollution. Duplicate lifecycle posting is also real, but it is the **second** PR, not the first.

## Disagreement Resolved

The two synthesis reports disagree on priority:

- GPT-5.4 synthesis: fix WATCHLIST lifecycle admission first.
- Claude synthesis: fix lifecycle idempotency first.

**Canonical resolution:** choose **WATCHLIST lifecycle segregation first**.

Reason:
1. It is an end-to-end, code-proven contradiction between doctrine and runtime.
2. It contaminates downstream quality evidence by letting preview-tier signals behave like paid tracked trades.
3. It explains why low-confidence outcomes appear in the monitored live lifecycle at all.
4. The doctrine is already explicit in `OWNER_BRIEF.md`, so this is not a genuinely open policy question on current `main`.

Claude is stronger on the duplicate-post mechanics, but GPT-5.4 is stronger on overall prioritization.

## What Is Confirmed

1. **WATCHLIST becomes a paid active signal on `360_SCALP`.**
   - Tiering defines WATCHLIST as `50–64` (`src/scanner/__init__.py:383-402`).
   - Scanner preserves WATCHLIST for scalp-family channels (`src/scanner/__init__.py:2942-2953`).
   - Router bypasses min-confidence for `360_SCALP` WATCHLIST (`src/signal_router.py:628-647`).
   - Router posts via the paid channel map and stores the signal in `_active_signals` (`src/signal_router.py:663-756`, `config/__init__.py:770-791`).
   - Trade monitor evaluates all active signals with no WATCHLIST exclusion (`src/trade_monitor.py:367-403`).

2. **That runtime contradicts documented doctrine.**
   - `OWNER_BRIEF.md` says `WATCHLIST | 50–64 | Post to free channel only` (`OWNER_BRIEF.md:467-474`).

3. **The scanner WATCHLIST comment is false as written.**
   - The comment says entry/SL/TP are cleared for zone-alert-only format, but the branch only populates context and returns the full signal (`src/scanner/__init__.py:2951-2953`).

4. **Router pulse logic already treats WATCHLIST as non-live-status material.**
   - `_signal_pulse_loop()` skips WATCHLIST-tier signals (`src/signal_router.py:354-362`).

5. **Duplicate lifecycle output has real code-level causes.**
   - Stop-style exits send `_post_update()` and then `_post_signal_closed(..., is_tp=False)` by design (`src/trade_monitor.py:634-650`, `src/trade_monitor.py:957-1010`).
   - Expiry has split ownership between `TradeMonitor` and `SignalRouter.cleanup_expired()` (`src/trade_monitor.py:552-560`, `src/signal_router.py:1109-1140`).
   - `_post_update()` has no exception handling, and terminal branches do not use `try/finally` around removal (`src/trade_monitor.py:552-560`, `src/trade_monitor.py:599-610`, `src/trade_monitor.py:634-650`, `src/trade_monitor.py:667-670`, `src/trade_monitor.py:931-955`).

6. **`SR_FLIP_RETEST` is the strongest confirmed family-level widening concern.**
   - It blocks only `VOLATILE` and stacks multiple soft penalties that can still leave the path alive (`src/channels/scalp.py:1777-1778`, `src/channels/scalp.py:1837`, `src/channels/scalp.py:1855-1862`, `src/channels/scalp.py:1887-1893`, `src/channels/scalp.py:1905`).

7. **The existing free publish helper is not a WATCHLIST route.**
   - `_maybe_publish_free_signal()` is once-per-day condensed output and requires confidence `>= 75` (`src/signal_router.py:897-926`).

8. **Current tests encode runtime behavior, not doctrine.**
   - `tests/test_pr18_scalp_tier_dispatch_alignment.py` asserts a `WATCHLIST` `360_SCALP` signal should dispatch (`tests/test_pr18_scalp_tier_dispatch_alignment.py:194-207`).

## What Remains Uncertain

1. **Exact live family concentration right now.**
   The source investigations cite monitor-log evidence for recent live losses and funnel counts, but that monitor-log ref was not available in the local clone during this merge pass. The code-supported ranking is strong; the exact latest live proportions remain secondary evidence from the source reports.

2. **The precise production trigger of duplicate `INVALIDATED` messages.**
   Code confirms a re-fire risk from missing removal guarantees and no event idempotency, but code alone does not prove which transport/runtime condition produced the observed duplicate invalidation example.

3. **Whether stop-style dual posting should remain as product behavior.**
   It is currently by design, but whether that UX should be reduced to one message is a follow-on decision, not the main diagnosis.

## WATCHLIST Lifecycle Truth

The canonical truth is simple:

> Under current `main`, `WATCHLIST` is **not** preview-only for `360_SCALP`; it is treated as a paid tracked trade object.

The decisive path is:
1. `classify_signal_tier()` marks `50–64` as `WATCHLIST` (`src/scanner/__init__.py:383-402`).
2. Scanner preserves that signal for scalp-family channels (`src/scanner/__init__.py:2942-2953`).
3. Router bypasses the paid-channel min-confidence floor for `360_SCALP` WATCHLIST (`src/signal_router.py:628-647`).
4. Router posts it through the paid path and registers it in `_active_signals` (`src/signal_router.py:663-756`).
5. `TradeMonitor` manages it like any other active trade (`src/trade_monitor.py:367-403`).

So the lifecycle truth is: **doctrine says free-only preview; runtime says paid active lifecycle. Runtime is wrong relative to doctrine.**

## Duplicate Posting Root Cause

The canonical diagnosis has three layers:

1. **Primary true bug:** terminal-event branches post before guaranteed removal.
   - SL, invalidation, expiry, and cancellation post first, then remove.
   - `_post_update()` has no local exception handling.
   - Those branches do not use `try/finally`.
   - If send fails, `_remove()` can be skipped and the signal can re-fire on the next poll.

2. **Confirmed duplicate-looking behavior by design:** stop-style exits currently emit two messages.
   - `_post_update(...)`
   - `_post_signal_closed(..., is_tp=False)`

3. **Independent duplicate source:** expiry is posted by two owners.
   - `TradeMonitor` posts expiry.
   - `SignalRouter.cleanup_expired()` also posts expiry.

So the best single root-cause statement is:

> True repeated lifecycle duplicates are best explained by missing guaranteed removal plus missing event idempotency; stop-style double output is additionally built into the current design.

## Low-Confidence Overexpression Diagnosis

The canonical diagnosis is:

1. **Primary cause:** WATCHLIST governance leakage.
   Low-confidence `50–64` signals are entering the paid active lifecycle, so weak outcomes are guaranteed to appear in paid/live telemetry.

2. **Secondary confirmed contributor:** `SR_FLIP_RETEST`.
   It has the widest confirmed soft-penalty funnel and broad regime allowance, making it the strongest family-level source of borderline WATCHLIST/B-tier output.

3. **Lower-confidence family claims:**
   - `TREND_PULLBACK_EMA` weak live expression is better explained by WATCHLIST admission than by a clearly broken evaluator.
   - `CONTINUATION_LIQUIDITY_SWEEP` is plausible but not proven dominant.

So the low-confidence overexpression diagnosis is:

> The system is mainly overexpressing low-confidence trades because WATCHLIST objects are admitted into the paid lifecycle; within that contaminated funnel, `SR_FLIP_RETEST` is the clearest path-level widening concern.

## What Should NOT Be Changed Yet

1. Do **not** broadly retune global confidence thresholds.
2. Do **not** broadly rewrite the scoring engine.
3. Do **not** broadly retune `TREND_PULLBACK_EMA` yet.
4. Do **not** broadly retune `CONTINUATION_LIQUIDITY_SWEEP` yet.
5. Do **not** treat a TradeMonitor-only WATCHLIST filter as the primary fix.
6. Do **not** reuse `_maybe_publish_free_signal()` unchanged as the WATCHLIST solution.
7. Do **not** redesign the whole architecture before fixing the narrow proven routing and lifecycle defects.

## Recommended Next PR

**WATCHLIST lifecycle segregation / doctrine alignment**

Scope:
1. Stop `WATCHLIST` from entering the paid active lifecycle.
2. Do not register `WATCHLIST` signals in `_active_signals`.
3. Implement an explicit free/watchlist route that matches doctrine instead of reusing the current paid path or the current `>= 75` free helper.
4. Update the false scanner comment.
5. Update tests and docs that currently encode the wrong runtime behavior.

Why this is the single best next PR:
- It fixes the clearest proven integrity failure.
- It removes the main source of low-confidence paid/live contamination.
- It makes post-fix telemetry interpretable before any family-level tuning.
- It resolves the direct contradiction between `OWNER_BRIEF.md` and runtime behavior.

**Next after that:** lifecycle idempotency / duplicate-post hardening.
