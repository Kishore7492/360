# Deep Technical Investigation: Live 360_SCALP Signal Expression Quality, Lifecycle Correctness, and Routing/Governance Integrity

- **Date:** 2026-04-14
- **Repository:** `mkmk749278/360-v2`
- **Branch investigated:** `main`
- **Model used:** Claude Opus 4.6
- **Scope:** Full code-path investigation of WATCHLIST→active lifecycle trace, duplicate lifecycle posting, confidence/tier/routing semantics, setup-family quality concentration, trade-monitor lifecycle, and docs-vs-code governance compliance.

---

## 1. Executive Summary

The live 360_SCALP engine is running and producing signals, but two concrete bugs and one critical governance mismatch are degrading live signal expression quality:

1. **WATCHLIST signals (confidence 50–64) are being posted to the PAID channel and entering the full trade monitor lifecycle.** OWNER_BRIEF.md explicitly states WATCHLIST should "Post to free channel only." The code bypasses the router min-confidence gate for WATCHLIST on 360_SCALP (PR-18, signal_router.py:633–640) but then continues through the paid-channel posting path (line 663–683), registers the signal as active (line 746), and admits it to the trade monitor. This directly causes low-confidence setups to enter lifecycle tracking, produce fast SL hits and invalidations, and pollute signal quality metrics.

2. **Duplicate lifecycle posts (SL HIT, INVALIDATED, EXPIRED) can occur when Telegram delivery fails mid-sequence.** The trade monitor's `_evaluate_signal` sets terminal status and calls `_post_update` before `_remove`. If `_post_update` throws (e.g., Telegram API error), `_remove` is never reached, the signal persists, and the next poll cycle re-fires the same event — posting a duplicate. The SL check (trade_monitor.py:634) and invalidation check (line 657) have no terminal-status guards. This is the likely root cause of observed duplicate invalidation/SL-style posts.

3. **SR_FLIP_RETEST has the most permissive soft-penalty structure** among the overrepresented setup families, with up to 20 points of cumulative soft penalties that frequently land signals in the 50–64 WATCHLIST zone. Combined with governance bug #1, these weak signals enter the paid channel and lifecycle tracking. TREND_PULLBACK_EMA is somewhat less affected (strict regime+EMA+RSI+SMC hard gates), but still contributes when base scores are moderate.

**Bottom line:** The core issue is not evaluator quality or scoring architecture — it is a governance-routing mismatch where WATCHLIST-tier signals bypass the min-confidence gate and enter the paid channel + trade monitor instead of being routed exclusively to the free channel. Fix the routing, and the weak signal expression problem is structurally resolved without touching evaluators or thresholds.

---

## 2. What Is Confirmed vs Unconfirmed

### Confirmed (code-verified)

| Finding | Evidence |
|---------|----------|
| WATCHLIST (50–64) signals bypass router min-confidence gate for 360_SCALP | `signal_router.py:633–640` |
| After bypass, WATCHLIST signals post to PAID channel (not free) | `signal_router.py:663–683` (same path as A+/B) |
| WATCHLIST signals register in `_active_signals` and enter trade monitor | `signal_router.py:746`, `trade_monitor.py:368` |
| OWNER_BRIEF.md tier table says WATCHLIST = "Post to free channel only" | `OWNER_BRIEF.md:471` |
| Scanner comment at line 2951 says "clear entry/SL/TP for zone-alert-only format" but does NOT clear them | `scanner/__init__.py:2951–2953` |
| SL check has no terminal-status guard — relies entirely on `_remove()` | `trade_monitor.py:634` |
| Invalidation check has no terminal-status guard at function entry | `trade_monitor.py:418–535` |
| `_post_update()` has no exception handling and no dedup guard | `trade_monitor.py:931–955` |
| If `_post_update` throws, `_remove()` is never reached → signal re-evaluated next cycle | `trade_monitor.py:634–651` |
| `_post_signal_closed()` HAS try/except (safe) | `trade_monitor.py:957–1010` |
| Router `_process()` has no signal_id dedup check at entry | `signal_router.py:482` |
| Delivery retry re-queues signal without dedup, can cause duplicate initial posts | `signal_router.py:691–721` |
| SR_FLIP_RETEST has up to 20pts cumulative soft penalties | `channels/scalp.py:1836–1862, 1887–1893, 1903–1905` |
| TREND_PULLBACK_EMA has strict hard gates (regime, EMA, RSI, SMC) | `channels/scalp.py:609–764` |
| Signal pulse loop correctly skips WATCHLIST signals | `signal_router.py:357` |
| Free channel requires confidence ≥ 75 (blocks most WATCHLIST) | `signal_router.py:914` |
| Trade monitor TP1/TP2/TP3 status guards are correct and prevent duplicate TP posts | `trade_monitor.py:677, 696, 714` |
| FreeWatchService has strong deduplication (dedupe key, cooldown, status check) | `free_watch_service.py:155–180` |

### Unconfirmed (requires live telemetry to verify)

| Hypothesis | Why unconfirmed |
|------------|-----------------|
| TREND_PULLBACK_EMA and SR_FLIP_RETEST are overrepresented in current live output | No live telemetry access; confirmed structurally possible but frequency requires runtime counters |
| Duplicate lifecycle posts are actively occurring in production | Reported by user; confirmed possible via code; exact frequency unknown |
| Telegram `_send` sometimes succeeds but returns False | Depends on Telegram API behavior; would explain router retry duplicates |

---

## 3. WATCHLIST Lifecycle Truth

### The question

Is WATCHLIST just an informational preview? Or can WATCHLIST candidates become full active/tracked signals?

### The answer: WATCHLIST candidates DO become full active/tracked signals — and this contradicts governance docs.

**Full trace:**

1. **Scanner creates WATCHLIST signal** — `classify_signal_tier()` at `scanner/__init__.py:383–402` assigns tier "WATCHLIST" for confidence 50–64. Tier is re-classified after soft penalty deduction at line 2745.

2. **Scanner preserves WATCHLIST** — At `scanner/__init__.py:2942–2953`, signals with `signal_tier == "WATCHLIST"` and `chan_name in _SCALP_CHANNELS` bypass the standard `min_conf` gate and are returned for dispatch. The comment at line 2951 says "clear entry/SL/TP for zone-alert-only format" but `_populate_signal_context()` does NOT clear entry/SL/TP — it only adds market context metadata (`market_phase`, `regime_context`, liquidity data).

3. **Scanner enqueues WATCHLIST signal** — The signal enters the dispatch path through `_scan_symbol()` and is placed in the signal queue to the router.

4. **Router bypasses min-confidence** — At `signal_router.py:633–640`:
   ```python
   if (
       getattr(signal, "signal_tier", "") == "WATCHLIST"
       and signal.channel == "360_SCALP"
   ):
       log.debug("WATCHLIST signal ... bypassing router min-confidence floor")
   ```
   This bypass allows the signal to continue through the router rather than being filtered at line 647.

5. **Router posts to PAID channel** — After the bypass, the signal follows the identical path as A+/B signals:
   - Risk check (line 649–661)
   - Paid channel lookup via `CHANNEL_TELEGRAM_MAP` (line 664)
   - Format and send to Telegram premium channel (lines 669–683)
   - Register in `_active_signals` (line 746)
   - Set `_position_lock` (line 747)
   - Trigger `observer.capture_entry_snapshot()` (line 761)
   - Trigger `on_signal_routed` callback (line 769)

6. **Trade monitor tracks WATCHLIST signal** — `TradeMonitor._check_all()` at `trade_monitor.py:367–403` fetches all signals from `router.active_signals` — there is NO tier filter. WATCHLIST signals are evaluated identically to A+/B signals: SL/TP checks, invalidation, trailing stops, DCA.

### Governance violation

| Source | What it says |
|--------|-------------|
| `OWNER_BRIEF.md:471` | `WATCHLIST \| 50–64 \| Post to free channel only` |
| `OWNER_BRIEF.md:457` | "WATCHLIST (50–64) semantics for 360_SCALP are now correctly preserved through router dispatch (PR-18)" |
| `OWNER_BRIEF.md:474` | "The tier table above is the current enforced doctrine." |

**Reality:** The code posts WATCHLIST to the paid channel and enters full lifecycle. PR-18 preserved WATCHLIST from being *filtered out* by the min-confidence gate but did NOT redirect WATCHLIST to the free channel. The governance docs and code are directly contradictory.

### Impact

WATCHLIST signals (confidence 50–64) with full entry/SL/TP data enter the trade monitor. Because they have lower confidence, they are structurally more likely to:
- Hit SL quickly (weaker thesis)
- Get invalidated by regime/momentum shifts (less margin)
- Produce fast "stopped out" or "invalidated" lifecycle posts

This directly explains the observed pattern of "many low-confidence WATCHLIST-originating setups progressing into tracked trade lifecycle events, with many fast SL hits or invalidations."

---

## 4. Duplicate Posting Root Cause

### Primary cause: Missing terminal-status guard + missing try/finally in trade monitor

The trade monitor `_evaluate_signal()` method (`trade_monitor.py:537–800`) has a structural vulnerability in ALL terminal-event handling blocks.

**The pattern (exemplified by SL check at lines 634–642):**

```python
if is_long and price <= sig.stop_loss:
    self._set_realized_pnl(sig, sig.stop_loss)         # Step 1: Set PnL
    outcome_label = self._apply_final_outcome(...)       # Step 2: Set status
    outcome_event = _STOP_OUTCOME_MESSAGES.get(...)
    await self._post_update(sig, outcome_event)          # Step 3: Post to Telegram ← CAN THROW
    self._record_outcome(sig, hit_tp=0, hit_sl=True)     # Step 4: Record metrics
    await self._post_signal_closed(sig, is_tp=False)     # Step 5: AI post (has own try/except)
    self._remove(sig.signal_id)                          # Step 6: Remove signal ← NEVER REACHED IF STEP 3 THROWS
    return
```

**Failure scenario:**
1. SL detected, status set to `"SL_HIT"` by `_apply_final_outcome` (step 2)
2. `_post_update` raises exception (Telegram API timeout, rate limit, network error)
3. Exception propagates through `_process_signal` → `asyncio.gather` → `_check_all` → `start()` where it's caught by the outer `except Exception` at line 359
4. Signal remains in `_active_signals` (step 6 never ran)
5. Next poll cycle: signal is fetched again
6. SL check at line 634: `is_long and price <= sig.stop_loss` — **NO status check** — fires again
7. `_post_update` called again — **DUPLICATE LIFECYCLE POST**

**The same vulnerability exists for:**
- SL SHORT (lines 643–651)
- INVALIDATED (lines 657–673)
- EXPIRED (lines 552–560)
- CANCELLED (lines 592–611)

**Why TP hits are NOT affected:**
TP1 and TP2 checks have explicit status guards:
- TP1: `sig.status not in ("TP1_HIT", "TP2_HIT", "TP3_HIT")` (line 714/773)
- TP2: `sig.status not in ("TP2_HIT", "TP3_HIT")` (line 696/756)
- TP3: `sig.status != "TP3_HIT"` (line 677/737) + immediate removal

These guards prevent re-posting even if `_remove()` fails. The SL, invalidation, expiry, and cancellation blocks lack equivalent guards.

### Secondary cause: Router retry without signal_id dedup

`signal_router.py:691–702`: If `_send_telegram` returns `False` (delivery failure), the signal is re-queued. At `_process()` entry (line 482), there is NO check for `signal.signal_id in self._active_signals`. If the first delivery actually succeeded (e.g., message sent but acknowledgment lost), the retry would post the initial signal announcement to Telegram again.

However, this secondary cause affects only the initial signal announcement, not lifecycle events (SL/TP/invalidation).

### The smallest correct fix

**For duplicate lifecycle posts (primary cause):**

Wrap the terminal-event block in try/finally to ensure `_remove()` always runs:

```python
if is_long and price <= sig.stop_loss:
    self._set_realized_pnl(sig, sig.stop_loss)
    outcome_label = self._apply_final_outcome(sig, hit_tp=0, hit_sl=True)
    outcome_event = _STOP_OUTCOME_MESSAGES.get(outcome_label, "🔴 EXIT")
    try:
        await self._post_update(sig, outcome_event)
        self._record_outcome(sig, hit_tp=0, hit_sl=True)
        await self._post_signal_closed(sig, is_tp=False)
    finally:
        self._remove(sig.signal_id)
    return
```

Apply the same pattern to SHORT SL (lines 643–651), INVALIDATED (lines 657–673), EXPIRED (lines 552–560), and CANCELLED (lines 592–611).

**Defense-in-depth:** Add an early return for already-terminal signals at the top of `_evaluate_signal`:

```python
_TERMINAL_STATUSES = {"SL_HIT", "INVALIDATED", "EXPIRED", "CANCELLED",
                      "BREAKEVEN_EXIT", "PROFIT_LOCKED", "FULL_TP_HIT"}
if sig.status in _TERMINAL_STATUSES:
    self._remove(sig.signal_id)
    return
```

**For router retry duplicates (secondary cause):**

Add signal_id dedup check at the start of `_process()`:

```python
if signal.signal_id in self._active_signals:
    log.info("Duplicate signal_id {} – already active, skipping", signal.signal_id)
    return
```

---

## 5. Confidence/Tier/Routing Truth

### Current tier thresholds

| Tier | Confidence | Scanner behavior | Router behavior (actual) | OWNER_BRIEF (intended) |
|------|-----------|-----------------|------------------------|----------------------|
| A+ | 80–100 | Passes all gates | Posted to paid channel, enters lifecycle | Fire to paid channel |
| B | 65–79 | Passes all gates | Posted to paid channel, enters lifecycle | Fire to paid channel |
| WATCHLIST | 50–64 | Bypasses min_conf gate for SCALP channels | **Posted to PAID channel, enters lifecycle** | **Post to FREE channel only** |
| FILTERED | < 50 | Rejected | Never reaches router | Reject — never dispatched |

### The tier/routing contradiction

- `config/__init__.py:579`: `MIN_CONFIDENCE_SCALP = 65` (lowered from 80 by PR-18)
- `scanner/__init__.py:2942–2953`: WATCHLIST signals bypass `min_conf` for SCALP channels
- `signal_router.py:633–640`: WATCHLIST signals bypass router min-confidence for `360_SCALP`
- `signal_router.py:663–746`: After bypass, follows the SAME paid-channel posting + lifecycle registration path

The net effect: **every signal with confidence ≥ 50 from a SCALP channel enters the paid channel and trade monitor**, despite the doctrine saying only ≥ 65 should reach paid.

### Signal pulse handling (correct)

The signal pulse loop at `signal_router.py:354–362` correctly skips WATCHLIST signals, so they don't receive periodic status updates. But this is moot if the signal still enters the trade monitor — it still gets SL/TP/invalidation lifecycle posts.

### Free channel handling (correct but irrelevant)

`_maybe_publish_free_signal()` at `signal_router.py:914` requires `confidence >= 75`, which correctly blocks WATCHLIST signals from the free channel. But this is the opposite of what should happen — WATCHLIST should be in the free channel, not the paid channel.

### Downstream impact on trade monitor admission

`TradeMonitor._check_all()` at `trade_monitor.py:367–403` has NO tier filter — it evaluates every signal in `_active_signals` uniformly. There is no mechanism to distinguish "informational preview" from "real live trade" once a signal is registered. This means the trade monitor cannot be the fix point — the fix must be in the router.

---

## 6. Setup-Family Quality Findings

### TREND_PULLBACK_EMA (`channels/scalp.py:609–764`)

- **Regime restriction:** Hard-gated to TRENDING_UP/TRENDING_DOWN only (line 622–627)
- **Key hard gates:** EMA9 > EMA21 > EMA50 alignment, price within 0.3% of EMA9 or 0.5% of EMA21, RSI 40–60, rejection candle, SMC FVG/orderblock presence
- **Confidence contribution:** +8 points (line 763)
- **Soft penalties:** None from evaluator itself (all gates are hard)
- **WATCHLIST production risk:** Moderate. The +8 boost from a ~55 base would reach 63 (WATCHLIST). But the hard gates are strict: trending regime + EMA triple alignment + RSI zone + SMC basis. When these are all met, the setup quality is reasonable. WATCHLIST instances likely occur when the composite scoring engine's base dimensions (SMC, volume, spread) are weak but the evaluator-specific conditions are met.
- **Quality assessment:** Not structurally flawed. The issue is that its WATCHLIST-tier output enters the paid channel.

### SR_FLIP_RETEST (`channels/scalp.py:1736–2006`)

- **Regime restriction:** Blocks VOLATILE only (line 1777–1778); allows most regimes
- **Key hard gates:** 8-candle lookback for flip detection, 0.6% proximity hard cap, wick ≥ 20% of body, EMA9 > EMA21, RSI < 80/> 20
- **Confidence contribution:** +8 points (line 1997)
- **Soft penalties (cumulative, up to 20pts total):**
  - Extended zone proximity (0.3–0.6%): +3 (line 1837)
  - Weak wick (20–50% of body): +4 (lines 1855–1856, 1861–1862)
  - Borderline RSI (70–79 / 21–30): +5 (lines 1887–1888, 1892–1893)
  - Missing SMC in FAST_STRUCTURAL regime: +8 (line 1905)
- **WATCHLIST production risk:** HIGH. With +8 base and up to 20pts of penalties, a signal scoring 70 pre-penalty can easily land at 50–58 post-penalty. The wide regime allowance (everything except VOLATILE) means this evaluator fires in more market conditions. The graduated penalty structure (proximity, wick, RSI, SMC are all soft) means many "borderline OK" setups pass all hard gates but accumulate soft penalties that push them into WATCHLIST zone.
- **Quality assessment:** The evaluator's design is reasonable (graduated severity), but the penalty structure creates a wide funnel into WATCHLIST. Combined with governance bug #1, these borderline setups enter the paid channel. **This is the most likely family driving observed weak signal expression.**

### CONTINUATION_LIQUIDITY_SWEEP (`channels/scalp.py:2534–2784`)

- **Regime restriction:** Hard-gated to TRENDING_UP/DOWN, STRONG_TREND, WEAK_TREND, BREAKOUT_EXPANSION only (line 2568)
- **Key hard gates:** EMA direction + regime cross-validation, ADX threshold, sweep presence within 10 candles, price reclaim confirmation, momentum confirmation
- **Confidence contribution:** None explicitly (no bonus like TREND_PULLBACK_EMA)
- **Soft penalties (up to 19pts):** RSI borderline +6, missing SMC +8, sweep recency 6–10 candles +5
- **WATCHLIST production risk:** Low-moderate. The regime + ADX + sweep reclaim gates are strict. The defining gate (price must have already reclaimed the swept level) is high-quality. WATCHLIST instances would require multiple soft penalties stacking.
- **Quality assessment:** Well-gated. Less likely to be a primary source of weak signals.

### Summary

| Evaluator | WATCHLIST risk | Primary driver of weak expression? |
|-----------|--------------|-----------------------------------|
| SR_FLIP_RETEST | HIGH (wide regime allowance, up to 20pts soft penalties) | **Yes — most likely** |
| TREND_PULLBACK_EMA | Moderate (strict hard gates, no soft penalties from evaluator) | Contributes when base scoring is weak |
| CONTINUATION_LIQUIDITY_SWEEP | Low-moderate (strict regime+ADX+reclaim gates) | Unlikely |

---

## 7. Governance Mismatches

### Mismatch #1: WATCHLIST routing (CRITICAL)

| Aspect | OWNER_BRIEF.md | Code reality |
|--------|---------------|-------------|
| WATCHLIST dispatch | "Post to free channel only" (`OWNER_BRIEF.md:471`) | Posts to paid channel (`signal_router.py:663–683`) |
| WATCHLIST lifecycle | Not described (implied: none, since free-only) | Full trade monitor lifecycle (SL/TP/invalidation) |
| PR-18 claim | "WATCHLIST semantics correctly preserved through router dispatch" (`OWNER_BRIEF.md:457`) | WATCHLIST bypasses min-confidence but follows paid path |
| Scanner comment | "clear entry/SL/TP for zone-alert-only format" (`scanner/__init__.py:2951`) | Does NOT clear entry/SL/TP |

### Mismatch #2: "zone-alert-only format" (MEDIUM)

The scanner comment at `scanner/__init__.py:2951` explicitly says WATCHLIST signals should be "zone-alert-only format" with cleared entry/SL/TP. The code does not implement this. The signal retains full trading data, which enables the trade monitor to process it as a real trade.

### Mismatch #3: Trade monitor admission scope (LOW)

`OWNER_BRIEF.md` describes the trade monitor as resolving "live paid-channel signals." The monitor has no mechanism to exclude non-paid signals. In the current code, any signal in `_active_signals` is monitored, regardless of tier. This is not a code bug per se — it's an architectural assumption that only paid-grade signals enter `_active_signals`, which is violated by governance mismatch #1.

### Mismatch #4: Radar alert completeness (INFORMATIONAL)

Per `docs/AUDIT_2026-04-13_FREE_CHANNEL_WATCH_LIFECYCLE_REPORT.md`, the `FreeWatchService` and radar alert lifecycle have been implemented. However, the radar path is only for soft-disabled channels. WATCHLIST-tier signals from active 360_SCALP do NOT use the radar/free-watch path — they go through the paid channel path instead.

---

## 8. Immediate Bugs to Fix Now

### Bug #1: WATCHLIST signals routed to paid channel instead of free (CRITICAL)

**File:** `signal_router.py:633–640`
**Impact:** Low-confidence signals (50–64) enter paid channel and full lifecycle, causing fast SL hits and invalidations that degrade signal quality.
**Fix:** After the WATCHLIST bypass, redirect to the free channel instead of continuing through the paid path. Or: don't bypass the min-confidence gate at all — let WATCHLIST signals take the radar/free-watch path instead.

### Bug #2: Duplicate lifecycle posts from missing try/finally (HIGH)

**File:** `trade_monitor.py:634–651, 643–651, 552–560, 592–611, 657–673`
**Impact:** SL/invalidation/expiry posts can fire twice if Telegram delivery fails mid-sequence.
**Fix:** Wrap terminal event blocks in try/finally to ensure `_remove()` always executes. Add early-return guard for terminal statuses at top of `_evaluate_signal`.

### Bug #3: Dead comment in scanner WATCHLIST path (LOW)

**File:** `scanner/__init__.py:2951`
**Impact:** Misleading comment; no functional impact.
**Fix:** Either implement the clearing (if zone-alert-only is desired) or remove the comment.

---

## 9. Best Next PR Recommendation

### PR #1 (Highest priority): Fix WATCHLIST routing governance

**Scope:** `signal_router.py`
**Change:**
- After the WATCHLIST bypass at lines 633–640, route WATCHLIST signals to the free channel (not paid)
- Do NOT register WATCHLIST signals in `_active_signals`
- Do NOT enter trade monitor lifecycle for WATCHLIST
- Optionally: route WATCHLIST through the radar/free-watch path using `_maybe_publish_free_signal` with a lowered confidence threshold for WATCHLIST-tier signals, or create a dedicated WATCHLIST posting path
- Update scanner comment at `scanner/__init__.py:2951` to match behavior

**Why this is #1:** This single change eliminates the entire class of "weak WATCHLIST signals entering paid lifecycle and producing fast SL/invalidation" without touching evaluators, scoring, or thresholds. It's the smallest change with the largest impact.

**Risk:** Low. WATCHLIST signals are currently rare (50–64 range after full scoring + penalties). Paid channel output quality improves; no loss of signal coverage since B-tier (65–79) is unaffected.

### PR #2 (High priority): Fix duplicate lifecycle posting

**Scope:** `trade_monitor.py`
**Change:**
- Add try/finally to all terminal event blocks (SL, invalidation, expiry, cancellation) ensuring `_remove()` always executes
- Add terminal-status early-return guard at top of `_evaluate_signal`
- Add signal_id dedup check at top of `signal_router.py:_process()`

**Why this is #2:** Prevents duplicate Telegram posts which confuse users and distort metrics. Independent of PR #1 — both bugs should be fixed.

**Risk:** Very low. try/finally is a narrowly scoped change. The terminal-status guard is defense-in-depth with no behavioral change for normal operation.

### PR #3 (Medium priority, deferred): SR_FLIP_RETEST quality tightening

**Scope:** `channels/scalp.py` (SR_FLIP_RETEST evaluator)
**Change candidates:**
- Tighten the proximity hard cap from 0.6% to 0.4%
- Convert the "missing SMC in FAST_STRUCTURAL" from soft penalty (+8) to hard gate
- Add regime restriction for QUIET (currently only VOLATILE is blocked)

**Why deferred:** After PR #1 fixes WATCHLIST routing, weak SR_FLIP_RETEST signals in the 50–64 range will no longer enter the paid channel. If B-tier (65–79) SR_FLIP_RETEST signals are also showing quality issues, THEN this PR becomes necessary. Monitor post-PR-1 before deciding.

---

## 10. Deferred Items That Should NOT Be Changed Yet

### Do NOT lower the WATCHLIST floor (50)

The 50–64 tier boundary is architecturally sound. The problem is routing, not the threshold.

### Do NOT add tier filtering to TradeMonitor

The monitor correctly evaluates all signals in `_active_signals`. The fix should prevent WATCHLIST from entering `_active_signals`, not add conditional logic inside the monitor.

### Do NOT redesign the free-watch/radar architecture

The `FreeWatchService` and radar pipeline are correctly designed for their use case (soft-disabled channels). The WATCHLIST routing fix should use the existing free-channel infrastructure, not create a new subsystem.

### Do NOT change the composite scoring engine

The scoring engine is producing correct scores — the problem is downstream routing of correctly-scored-but-low-confidence signals.

### Do NOT tighten TREND_PULLBACK_EMA gates

This evaluator has appropriate hard gates. Its WATCHLIST-tier output is a legitimate quality tier that should go to the free channel, not be eliminated.

### Do NOT change the signal pulse loop WATCHLIST guard

The pulse loop correctly skips WATCHLIST signals (`signal_router.py:357`). This guard is correct and should be preserved.

### Do NOT add broad redesigns to the signal format

The signal formatting and Cornix integration work correctly. No changes needed.

---

## Appendix A: Key File/Function Reference

| Component | File | Key Lines |
|-----------|------|-----------|
| Tier classification | `scanner/__init__.py` | 383–402 (classify_signal_tier) |
| WATCHLIST scanner bypass | `scanner/__init__.py` | 2942–2953 |
| Soft penalty accumulation | `scanner/__init__.py` | 2622–2623, 2728–2745 |
| Router WATCHLIST bypass | `signal_router.py` | 633–640 |
| Paid channel dispatch | `signal_router.py` | 663–683 |
| Active signal registration | `signal_router.py` | 746–748 |
| Signal pulse WATCHLIST guard | `signal_router.py` | 354–362 |
| Free channel confidence gate | `signal_router.py` | 914 |
| Delivery retry (no dedup) | `signal_router.py` | 691–721 |
| Router _process entry (no signal_id check) | `signal_router.py` | 482 |
| Trade monitor poll loop | `trade_monitor.py` | 367–403 |
| SL check (no status guard) | `trade_monitor.py` | 634–651 |
| Invalidation check | `trade_monitor.py` | 657–673 |
| _post_update (no dedup, no try/except) | `trade_monitor.py` | 931–955 |
| _post_signal_closed (has try/except) | `trade_monitor.py` | 957–1010 |
| _remove (synchronous, correct) | `signal_router.py` | 1065–1071 |
| TREND_PULLBACK_EMA evaluator | `channels/scalp.py` | 609–764 |
| SR_FLIP_RETEST evaluator | `channels/scalp.py` | 1736–2006 |
| CONTINUATION_LIQUIDITY_SWEEP evaluator | `channels/scalp.py` | 2534–2784 |
| FreeWatchService (correct dedup) | `free_watch_service.py` | 71–316 |
| TradeObserver (correct idempotency) | `trade_observer.py` | 213–596 |
| OWNER_BRIEF tier table | `OWNER_BRIEF.md` | 467–472 |
| Config channel min_confidence | `config/__init__.py` | 569–695 |

## Appendix B: Lifecycle State Machine (Verified)

```
                           ┌── Signal created by Scanner ──┐
                           │                                │
                           ▼                                │
                     ┌──────────┐                           │
                     │  ACTIVE  │◄── Registered in _active_signals
                     └────┬─────┘    after Telegram delivery
                          │
            ┌─────────────┼─────────────┬──────────────┐
            ▼             ▼             ▼              ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
      │  SL_HIT  │  │INVALIDATED│  │ EXPIRED  │  │CANCELLED │
      │(no guard)│  │(no guard) │  │(no guard)│  │(no guard)│
      └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
           │              │             │              │
           ▼              ▼             ▼              ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ _remove  │  │ _remove  │  │ _remove  │  │ _remove  │
      │ (if      │  │ (if      │  │ (if      │  │ (if      │
      │ reached) │  │ reached) │  │ reached) │  │ reached) │
      └──────────┘  └──────────┘  └──────────┘  └──────────┘

            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ TP1_HIT  │  │ TP2_HIT  │  │ TP3_HIT  │
      │(guarded) │  │(guarded) │  │(guarded) │
      │continues │  │continues │  │ removes  │
      └──────────┘  └──────────┘  └──────────┘

  "no guard" = re-fires if _remove() was not reached
  "guarded"  = status check prevents duplicate posts
```

---

*End of investigation report.*
