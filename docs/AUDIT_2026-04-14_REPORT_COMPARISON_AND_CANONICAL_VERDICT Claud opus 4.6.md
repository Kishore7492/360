# Canonical Comparison & Verdict: Three-Model Live Signal Expression Investigation

- **Date:** 2026-04-14
- **Repository:** `mkmk749278/360-v2`
- **Branch:** `main`
- **Reports compared:**
  1. `docs/AUDIT_2026-04-14_LIVE_SIGNAL_EXPRESSION_INVESTIGATION_GPT-5.4.md` (hereafter **GPT-5.4**)
  2. `docs/AUDIT_2026-04-14_LIVE_SIGNAL_EXPRESSION_INVESTIGATION_CLAUDE-OPUS-4.6.md` (hereafter **Opus**)
  3. `docs/AUDIT_2026-04-14_LIVE_SIGNAL_EXPRESSION_INVESTIGATION_GPT-5.3-CODEX.md` (hereafter **Codex**)
- **Final recommended next PR:** Lifecycle idempotency + duplicate-post hardening in `trade_monitor.py` (with WATCHLIST routing fix as close second — see §8 for ranking rationale)

---

## 1. Areas Where All Three Reports Agree

All three reports converge on the following claims. Each has been re-verified against current `main` branch code during this synthesis.

| # | Consensus claim | Code verification |
|---|----------------|-------------------|
| 1 | **WATCHLIST (50–64) signals for `360_SCALP` bypass the router min-confidence gate and enter the paid channel + active lifecycle.** | Verified: `signal_router.py:633–640` bypasses min-conf; line 746 registers in `_active_signals`; `trade_monitor.py:367–403` evaluates them. |
| 2 | **This violates OWNER_BRIEF.md doctrine** which states WATCHLIST = "Post to free channel only." | Verified: `OWNER_BRIEF.md:471` tier table says free-only; code routes through `CHANNEL_TELEGRAM_MAP` to the paid channel at `signal_router.py:663–683`. |
| 3 | **Scanner comment at line 2951 says "clear entry/SL/TP for zone-alert-only format" but the code does NOT clear them.** The signal retains full executable geometry. | Verified: `scanner/__init__.py:2951–2953` — only `_populate_signal_context()` is called; no entry/SL/TP clearing. |
| 4 | **Router pulse loop correctly skips WATCHLIST** (`signal_router.py:354–362`), implicitly acknowledging WATCHLIST is not a true live trade. Yet trade monitor still tracks it. | Verified. |
| 5 | **No lifecycle-event idempotency guard exists in `TradeMonitor`.** `_post_update()` has no dedup, no `(signal_id, event)` ledger, no terminal-status check. | Verified: `trade_monitor.py:931–955` — builds text and sends; no guard. |
| 6 | **Stop-style exits (SL, breakeven, profit-locked) post TWO messages by design:** an explicit lifecycle update via `_post_update()` and then an AI "signal closed" summary via `_post_signal_closed()`.** | Verified: `trade_monitor.py:634–642` (long SL) calls `_post_update` + `_post_signal_closed` + `_remove` in sequence. |
| 7 | **Expiry has split ownership:** `TradeMonitor._evaluate_signal()` posts expiry AND `SignalRouter.cleanup_expired()` independently posts expiry. Both can fire for the same signal. | Verified: `trade_monitor.py:552–560` and `signal_router.py:1109–1146`. |
| 8 | **TP1/TP2/TP3 checks DO have status guards** that prevent duplicate posting. SL, invalidation, expiry, cancellation do NOT. | Verified: TP3 guarded by `sig.status != "TP3_HIT"` (line 677/737); TP2 by `not in ("TP2_HIT", "TP3_HIT")` (line 696/756); TP1 by `not in ("TP1_HIT", ...)` (line 714). SL at line 634 has no status guard. |
| 9 | **SR_FLIP_RETEST has the widest soft-penalty surface** (up to 20pts cumulative: proximity +3, wick +4, RSI +5, SMC +8) and the widest regime allowance (only VOLATILE blocked). | Verified: `channels/scalp.py:1777–1778` (VOLATILE block only), soft penalties at lines 1837, 1855–1862, 1887–1893, 1905. |
| 10 | **Tier thresholds:** A+ ≥ 80, B ≥ 65, WATCHLIST ≥ 50, FILTERED < 50. | Verified: `scanner/__init__.py:383–402`. |
| 11 | **Existing telemetry hooks** (`_setup_eval_counts`, `_setup_emit_counts`, `_scoring_tier_counters`) exist to audit family concentration — but tuning should follow governance and lifecycle fixes. | Verified. |

---

## 2. Areas Where the Reports Disagree

### 2A. Root cause of duplicate INVALIDATED posts

| Report | Claim | Assessment |
|--------|-------|------------|
| **Opus** | Primary cause is missing `try/finally` around `_post_update` → `_remove` — if `_post_update` throws, `_remove` is never reached, signal persists, and next poll re-fires the same terminal event. Provides specific code trace (lines 634–651). | **Strongest.** This is the mechanistic explanation with precise failure mode: SL check at line 634 has no status guard, so a persisted signal will re-fire. |
| **Codex** | Missing "event idempotency" guard. Does not distinguish the `try/finally` failure mode from generic idempotency. | Correct direction but less precise. |
| **GPT-5.4** | Same as Codex — calls it "missing idempotency guard" — but adds "transport retry duplication or the same signal object being re-processed after wider state/lifecycle reuse" as alternative triggers. | Adds plausible alternatives, but the `try/finally` gap is the strongest confirmed mechanism. |

**Verdict:** Opus's `try/finally` analysis is the most mechanistically precise. The missing terminal-status guard at SL/invalidation entry is the confirmed primary pathway. The generic idempotency concern (shared by all three) is a real defense-in-depth issue but secondary.

### 2B. Priority ordering: WATCHLIST routing fix vs lifecycle idempotency fix

| Report | Recommended PR #1 | Rationale |
|--------|-------------------|-----------|
| **GPT-5.4** | WATCHLIST lifecycle segregation | Biggest truth/integrity failure; prevents preview objects from becoming live trades. |
| **Opus** | WATCHLIST routing governance | Same rationale; calls it the single change with largest impact. |
| **Codex** | Lifecycle idempotency + duplicate-post hardening | Directly addresses visible production symptom (duplicate messages); smallest high-confidence patch surface. |

**Verdict:** This is a genuine tactical disagreement. Both priorities are high. The deciding factor:
- **WATCHLIST routing** requires a product decision (does the owner want to amend doctrine? keep free-only? keep paid-but-untracked?). Until that decision is explicit, implementation may be blocked.
- **Lifecycle idempotency** is a pure correctness bug with no policy ambiguity — every terminal event block should have `try/finally` + status guard regardless of WATCHLIST policy.

**This synthesis recommends: Lifecycle idempotency first (PR #1), WATCHLIST routing second (PR #2).** Rationale: the idempotency fix is unambiguous, independently valuable, and unblocked by policy decisions. The WATCHLIST fix should immediately follow once the owner confirms the routing policy.

### 2C. Severity of CONTINUATION_LIQUIDITY_SWEEP as a quality concern

| Report | Claim |
|--------|-------|
| **GPT-5.4** | Lists it in recent live losses and calls its funnel telemetry "not dominant." Calls it "present but not yet dominant." |
| **Opus** | Rates it "low-moderate WATCHLIST risk," well-gated (regime + ADX + reclaim), unlikely to be a primary source of weak signals. |
| **Codex** | Lists it as a third family with intentional soft penalties (RSI borderline, no FVG/OB, sweep recency) but groups it alongside SR_FLIP_RETEST as "borderline quality." |

**Verdict:** GPT-5.4 and Opus are most accurate — CONTINUATION_LIQUIDITY_SWEEP has strict hard gates and is not confirmed as a current primary driver. Codex slightly overweights it by grouping it with SR_FLIP_RETEST. The correct ranking is: SR_FLIP_RETEST >> TREND_PULLBACK_EMA (WATCHLIST leakage only) > CLS (not yet proven).

### 2D. TREND_PULLBACK_EMA: evaluator permissiveness vs WATCHLIST leakage

| Report | Claim |
|--------|-------|
| **GPT-5.4** | Calls it the dominant family in recent live resolved history (6/10). States its weak expression "looks less like evaluator permissiveness and more like WATCHLIST/tracking governance leakage." |
| **Opus** | "Not structurally flawed. The issue is that its WATCHLIST-tier output enters the paid channel." |
| **Codex** | Notes +8 confidence bump and no in-path soft penalty stack but doesn't separate governance leakage from evaluator quality. |

**Verdict:** GPT-5.4 and Opus agree and are correct — TREND_PULLBACK_EMA's hard gates are strict (trending regime, triple EMA alignment, RSI 40–60, SMC basis). Its weak live expression is primarily a WATCHLIST-routing problem, not an evaluator problem. Do not tighten TREND_PULLBACK_EMA gates.

### 2E. Router retry as a duplicate-initial-post vector

| Report | Claim |
|--------|-------|
| **Opus** | Identifies router delivery retry at `signal_router.py:691–702` + missing `signal_id` dedup at `_process()` entry (line 482) as a secondary duplicate-initial-post vector. Notes it affects only initial announcement, not lifecycle events. |
| **GPT-5.4** | Does not explicitly call out router retry dedup. |
| **Codex** | Does not mention router retry dedup. |

**Verdict:** Opus is correct. The router retry path can cause duplicate initial posts if Telegram acknowledged delivery but the bot received a transport error. This is secondary (affects initial post only, not lifecycle), but the fix is trivial (check `signal_id in _active_signals` at `_process` entry). Should be included in the lifecycle PR.

---

## 3. Claims Strongly Supported by Code

These claims are verified against current `main` and should be treated as established facts.

1. **WATCHLIST `360_SCALP` enters paid channel + active lifecycle.** (`signal_router.py:633–640, 663–683, 746`; `trade_monitor.py:367–403`)
2. **Doctrine says WATCHLIST = free-only.** (`OWNER_BRIEF.md:471`)
3. **SL/invalidation/expiry/cancel terminal blocks lack `try/finally` around `_remove()`.** If `_post_update` throws, signal persists and re-fires. (`trade_monitor.py:634–651, 657–673, 552–560`)
4. **TP status guards are correct and prevent TP duplicate posts.** (`trade_monitor.py:677, 696, 714`)
5. **`_post_signal_closed()` has its own `try/except` and is safe.** (`trade_monitor.py:957–1010`)
6. **`_post_update()` has no exception handling.** (`trade_monitor.py:931–955`)
7. **Scanner WATCHLIST comment is dead code — no clearing occurs.** (`scanner/__init__.py:2951–2953`)
8. **SR_FLIP_RETEST allows all regimes except VOLATILE and has up to 20pts soft penalties.** (`channels/scalp.py:1777–1778, 1837, 1855–1862, 1887–1893, 1905`)
9. **Expiry has dual posting paths.** (`trade_monitor.py:552–560` + `signal_router.py:1109–1146`)
10. **Free channel requires confidence ≥ 75, blocking WATCHLIST from the free path too.** (`signal_router.py:914`)

---

## 4. Claims That Are Speculative or Weak

| Claim | Source | Why weak |
|-------|--------|----------|
| "CONTINUATION_LIQUIDITY_SWEEP is a primary driver of weak signal expression" | Codex (implicit grouping) | Not supported by checked-in funnel telemetry; GPT-5.4 and Opus both rate it as non-dominant. Hard gates are strict. |
| "Duplicate INVALIDATED posts are caused by dual loop/process reality" | GPT-5.4 (listed as alternative) | Code has only one invalidation branch. The `try/finally` gap is the confirmed mechanism. Multi-process/loop duplication is possible but unproven and less likely than the simpler explanation. |
| "Transport retry duplication" as a lifecycle duplicate cause | GPT-5.4 | Router retry only affects initial announcement, not lifecycle events. Lifecycle events come from trade monitor which has no retry logic — they just fail or succeed. |
| "Current live overrepresentation of CLS" | GPT-5.4 (noted as unconfirmed) | Present in recent losing history but not dominant in last-100-cycle scoring counters. Correctly self-identified as unconfirmed. |

---

## 5. Best Explanation of WATCHLIST Lifecycle Truth

**Canonical answer (all three agree, verified against code):**

WATCHLIST is **not** informational-only in the current runtime for `360_SCALP`. The end-to-end lifecycle is:

1. `classify_signal_tier()` assigns tier "WATCHLIST" for confidence 50–64 (`scanner/__init__.py:383–402`).
2. `_prepare_signal()` re-classifies tier after soft penalty deduction (`scanner/__init__.py:2745`).
3. Scanner WATCHLIST short-circuit preserves the signal (with full entry/SL/TP geometry) for scalp channels (`scanner/__init__.py:2942–2953`). Despite the comment, no clearing occurs.
4. Signal enters `SignalRouter._process()` via queue.
5. Router bypasses min-confidence floor for `360_SCALP` WATCHLIST (`signal_router.py:633–640`).
6. Signal is posted to the paid channel via `CHANNEL_TELEGRAM_MAP` (`signal_router.py:663–683`).
7. Signal is registered in `_active_signals` (`signal_router.py:746`).
8. Trade monitor evaluates it identically to A+/B signals — SL, TP, invalidation, trailing stops, DCA — with no tier exclusion (`trade_monitor.py:367–403`).
9. Pulse loop correctly skips WATCHLIST for status pulses (`signal_router.py:354–362`), but this does not prevent lifecycle tracking.

**Governance status:** OWNER_BRIEF.md says "Post to free channel only" (`OWNER_BRIEF.md:471`). Code does the opposite. This is a confirmed governance mismatch.

**Strongest formulation:** Opus provides the most complete trace (steps 1–9 with exact line numbers), the lifecycle state machine diagram, and the clearest separation of "what doctrine says" vs "what code does." GPT-5.4 adds live monitor evidence. Codex is accurate but less detailed.

---

## 6. Best Explanation of Duplicate Lifecycle Posting Root Cause

**Canonical answer (Opus's formulation is strongest, verified against code):**

There are three confirmed duplicate-post vectors:

### Vector 1 (PRIMARY): Missing try/finally in terminal event blocks

SL, invalidation, expiry, and cancellation blocks follow this pattern:

```
status set → _post_update() → _record_outcome() → _post_signal_closed() → _remove()
```

If `_post_update()` throws (Telegram API error, rate limit, network timeout), `_remove()` is never reached. The signal persists in `_active_signals`. On the next poll cycle, the same terminal condition fires again (SL check at line 634 has **no status guard**), and `_post_update` is called again — producing a duplicate.

TP checks are safe because they have explicit status guards (`sig.status not in ("TP1_HIT", ...)`) that prevent re-firing.

**Evidence:** `trade_monitor.py:634–651` (SL), `657–673` (invalidation), `552–560` (expiry). None have `try/finally`. `_post_update` at lines 931–955 has no exception handling.

### Vector 2 (BY DESIGN): Dual-post stop-style close

For SL/breakeven/profit-locked outcomes, the code intentionally sends:
1. `_post_update(outcome_event)` — the lifecycle event ("🔴 SL HIT")
2. `_post_signal_closed(is_tp=False)` — an AI-written "signal closed" summary

Both go to the same active channel. This is design, not a bug, but looks like duplication to users.

### Vector 3 (CONFIRMED): Split expiry ownership

`TradeMonitor._evaluate_signal()` posts "⏰ EXPIRED" and `SignalRouter.cleanup_expired()` independently posts expiry notification. Because the monitor evaluates a snapshot of active signals, router-side removal does not prevent the monitor from also processing the signal in the same cycle.

### Smallest correct fix

1. Wrap all terminal-event blocks in `try/finally` ensuring `_remove()` always runs.
2. Add terminal-status early-return guard at top of `_evaluate_signal`: if `sig.status in _TERMINAL_STATUSES`, call `_remove` and return.
3. Consolidate expiry to single owner (recommend: trade monitor owns posting; router's `cleanup_expired` does silent removal only).
4. Product decision: keep dual-post close semantics or consolidate to single message.

---

## 7. Best Explanation of Low-Confidence Overexpression / Weak Live Quality

**Canonical answer (GPT-5.4 + Opus combined formulation):**

The observed weak live signal expression is a two-layer problem:

### Layer 1: WATCHLIST governance leakage (primary)

Signals scoring 50–64 enter the paid channel and full lifecycle. Under doctrine they should be free-only. These signals are structurally more likely to hit SL quickly or get invalidated, producing fast terminal events that degrade perceived quality. Fixing WATCHLIST routing eliminates this entire class.

### Layer 2: SR_FLIP_RETEST evaluator permissiveness (secondary, confirmed)

SR_FLIP_RETEST has the widest regime allowance (everything except VOLATILE) and up to 20pts of cumulative soft penalties. This creates a wide funnel: signals scoring 70+ pre-penalty can land at 50–58 post-penalty. Combined with Layer 1, these borderline setups enter the paid channel.

### Not a primary factor: TREND_PULLBACK_EMA and CONTINUATION_LIQUIDITY_SWEEP

- **TREND_PULLBACK_EMA** has strict hard gates. Its weak live expression is primarily a WATCHLIST leakage problem, not an evaluator design problem.
- **CONTINUATION_LIQUIDITY_SWEEP** has strict regime + ADX + reclaim gates and is not confirmed as a dominant current source.

### Key insight (from GPT-5.4)

Do not tune evaluator families before fixing WATCHLIST routing. Current live quality evidence is contaminated by governance leakage. After WATCHLIST is fixed, re-read telemetry to determine whether SR_FLIP_RETEST specifically needs tightening at the B-tier level.

---

## 8. Ranked Recommendation for Next PR

### PR #1: Lifecycle idempotency + duplicate-post hardening

**Scope:** `trade_monitor.py` (primary), `signal_router.py` (cleanup_expired consolidation + optional _process signal_id dedup)

**Changes:**
1. Wrap SL, invalidation, expiry, cancellation terminal blocks in `try/finally` ensuring `_remove()` always executes.
2. Add terminal-status early-return guard at top of `_evaluate_signal`.
3. Consolidate expiry posting to single owner (trade monitor owns posting; router does silent cleanup).
4. Add `signal_id in _active_signals` check at `_process()` entry (defense-in-depth for router retry).

**Why first:**
- Pure correctness bug with zero policy ambiguity.
- Directly fixes user-visible duplicate messages.
- Smallest patch surface, highest confidence.
- Unblocked — requires no product decision.

### PR #2: WATCHLIST routing governance alignment

**Scope:** `signal_router.py` (primary), `scanner/__init__.py` (comment fix)

**Changes:**
1. After WATCHLIST bypass at lines 633–640, route to free channel instead of paid channel.
2. Do NOT register WATCHLIST signals in `_active_signals`.
3. Update or remove dead scanner comment at line 2951.
4. Align tests (PR-18 test assertions may need updating).
5. Align ACTIVE_CONTEXT.md wording.

**Why second (not first):**
- Requires explicit owner decision: keep free-only doctrine? Or amend doctrine to paid-but-untracked?
- High impact once the policy question is answered.
- The free channel currently requires confidence ≥ 75 (`signal_router.py:914`), which would also block WATCHLIST. A dedicated WATCHLIST posting path or lowered free threshold is needed.

### PR #3: Evidence-gated SR_FLIP_RETEST quality review

**Scope:** `channels/scalp.py` (SR_FLIP_RETEST evaluator)

**Why third:**
- After PR #1 and #2, re-read live telemetry.
- If B-tier (65–79) SR_FLIP_RETEST signals still show quality problems, then tighten.
- Candidate changes: tighten proximity hard cap, convert "missing SMC in FAST_STRUCTURAL" from soft to hard gate, consider adding QUIET regime block.

---

## 9. Explicit Recommendation of What NOT to Change Yet

1. **Do NOT lower the WATCHLIST floor (50).** The threshold is correct; the problem is routing.
2. **Do NOT add tier filtering inside TradeMonitor.** Fix the admission point (router), not the consumer.
3. **Do NOT tighten TREND_PULLBACK_EMA gates.** Hard gates are strict; weak expression is governance leakage.
4. **Do NOT tighten CONTINUATION_LIQUIDITY_SWEEP.** Not confirmed as a dominant problem source.
5. **Do NOT broadly loosen spread/regime/MTF thresholds.** Current evidence is contaminated by WATCHLIST leakage.
6. **Do NOT redesign the signal architecture (queue/router/monitor).** Current failures are solvable with narrow targeted fixes.
7. **Do NOT change the scoring engine.** Scores are correct; routing of correctly-scored signals is wrong.
8. **Do NOT change the pulse loop WATCHLIST guard.** It is correct (`signal_router.py:357`).
9. **Do NOT redesign the free-watch/radar architecture.** It works for its use case (soft-disabled channels).

---

## 10. Final Canonical Verdict

### The core problem is not evaluator silence, scoring, or architecture. It is two specific bugs and one governance mismatch:

| # | Issue | Type | Impact | Fix complexity |
|---|-------|------|--------|----------------|
| 1 | Terminal-event blocks lack `try/finally` → duplicate posts when `_post_update` throws | **Bug** | User-visible duplicate messages, metric distortion | Low (narrow `trade_monitor.py` change) |
| 2 | Expiry has dual posting ownership (monitor + router) | **Bug** | Duplicate expiry messages | Low (consolidate to single owner) |
| 3 | WATCHLIST `360_SCALP` enters paid channel + active lifecycle despite free-only doctrine | **Governance mismatch** | Low-confidence signals tracked as real trades, fast SL/invalidation, degraded quality metrics | Medium (routing change + policy decision + test update) |

### Which report was strongest?

- **Opus** was the most mechanistically precise on duplicate-post root cause (`try/finally` gap, terminal-status guard asymmetry between SL and TP, lifecycle state machine). It also provided the clearest governance mismatch table and the most actionable fix proposals.
- **GPT-5.4** was the only report with live monitor evidence, giving it the strongest empirical basis for setup-family quality claims. Its three-meaning-of-WATCHLIST framing was the clearest governance analysis.
- **Codex** was accurate and well-organized but less detailed than the other two. It correctly prioritized lifecycle idempotency over WATCHLIST routing.

### Single recommended next action

**Open PR: "Lifecycle idempotency + duplicate-post hardening"**

Wrap all terminal-event blocks in `try/finally`, add terminal-status early-return guard, consolidate expiry posting to single owner, and add router `_process` signal_id dedup check. This is the highest-confidence, lowest-risk, zero-ambiguity fix that directly addresses the most visible production symptom.

Follow immediately with the WATCHLIST routing governance PR once the owner confirms the routing policy.

---

*End of canonical comparison and verdict report.*
