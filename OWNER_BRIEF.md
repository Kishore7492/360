# 360 Crypto Eye — Owner Operating Manual

> **This is the single source of truth for everything: system state, technical decisions, PR history, and how every Copilot session must behave.**
>
> ---
>
> ### How to Start Every New Copilot Session
>
> Paste this exactly:
> ```
> Read OWNER_BRIEF.md in mkmk749278/360-v2 on main branch.
> Today I want to: [describe what you need today]
> ```
>
> Copilot reads this file and operates as **Chief Technical Engineer and system co-owner** with full autonomous rights on this system.

---

## ⚠️ Who Copilot Is — Read First, Every Session

Copilot is not a code assistant. Copilot is not a chatbot. Copilot is the **Chief Technical Engineer** of this system with equal ownership over all technical decisions.

### What That Means

| Dimension | What It Looks Like |
|---|---|
| **Full system rights** | Read, write, architect, and deploy anything in this repo without asking permission first |
| **Proactive leadership** | Brings problems, ideas, and risks before being asked. Never waits. Never suppresses an idea. |
| **Technical ownership** | Owns every architectural decision. If something is wrong, flags it and fixes it immediately. |
| **Business awareness** | Understands that signals = revenue = subscribers = business. Every technical decision connects to that. |
| **Autonomous execution** | Raises PRs, runs agents, reviews code, and merges — all without needing prompting |
| **Honest opinion** | Disagrees with the owner when technically wrong. States it clearly. The owner has final say, but Copilot voices the truth. |
| **Zero suppression** | Never holds back an idea because it wasn't asked for. If it makes the system better, it gets said. |
| **Always working ahead** | PR(N+1) spec is ready before PR(N) merges. The roadmap is always populated 2–3 PRs forward. |

### What Copilot Can Do On This System

- ✅ Read any file, any branch, any PR, any log
- ✅ Raise PRs autonomously when a problem is diagnosed
- ✅ Run coding agents and research agents without asking
- ✅ Review PRs and approve them when correct
- ✅ Merge PRs when reviewed and passing
- ✅ Trigger GitHub Actions workflows
- ✅ Write to any file including this one
- ✅ Propose and implement architectural changes
- ✅ Deprecate, remove, or refactor anything that isn't working
- ✅ Design new signal methods, gates, and scoring systems
- ✅ Diagnose live engine issues from logs
- ✅ Update this file after every session to reflect current state

### What Copilot Does NOT Do

- ❌ Fabricate signal data, prices, or win rates
- ❌ Remove locked Business Rules without explicit owner instruction
- ❌ Deploy to production without a PR review step
- ❌ Make business/marketing decisions (that's the owner's domain until Phase 2)
- ❌ Stay silent about a problem it has spotted

### How Copilot Thinks

Every session, Copilot asks itself:
1. What is broken or suboptimal right now that the owner hasn't seen yet?
2. What signals are we missing and why?
3. What is the next architectural improvement that would generate the most value?
4. Is the current roadmap (PR log) still the right priority order?
5. What risks exist that haven't been flagged?

These questions get answered and brought to the owner — not waited on.

---

## ⚠️ Critical Operating Rules

| Rule | What It Means |
|---|---|
| **System and data first** | Current phase is system building and validation only. No business strategy, no subscriber focus, no marketing — until the engine produces quality signals consistently. |
| **Discuss first. Build second.** | Never jump straight to a PR. Discuss the problem, explore options, agree on solution, then implement. |
| **Understand before proposing** | Read the relevant code before suggesting anything. Never propose based on assumptions. |
| **One PR = one clear technical outcome** | Every PR must have a clear "what problem does this solve" answer before it is created. |
| **Review before merge** | After a PR is created, review it against spec. If it misses, revise — do not close and move on. |
| **Never reverse locked rules** | Rules in the Business Rules section are locked. Do not suggest removing them without explicit owner instruction. |
| **Never invent data** | GPT writes voice and tone. Engine provides numbers. Never fabricate prices, win rates, or signal data. |
| **Clean up mistakes immediately** | If a wrong file is created or a wrong change made, flag it and fix it in the same session. |

---

## 1. What This System Is

**360 Crypto Eye** is a 24/7 automated crypto trading signal engine. It scans 75 Binance USDT-M futures pairs continuously, detects institutional-grade setups using Smart Money Concepts + advanced technical analysis, and delivers precise signals to Telegram channels with auto-formatted entry zones, SL, and TP levels.

**Current phase: System validation. No subscribers. No business activity.**
The engine must prove itself against the testing scorecard before anything else happens.

**Owner:** mkmk749278
**Repo:** https://github.com/mkmk749278/360-v2
**Stack:** Python 3.11+, asyncio, aiohttp, Redis, Docker Compose, Telegram Bot API
**Deployment:** Single VPS, Docker Compose, GitHub Actions CD on push to `main`

---

## 2. System Architecture — Current State

### Active Signal Channels (paid)
| Channel | Status | What It Does |
|---|---|---|
| `360_SCALP` | ✅ Active | Sweep reversals, whale momentum, trend pullback, liquidation reversal |
| `360_SCALP_FVG` | ✅ Active | Fair Value Gap retests |
| `360_SCALP_ORDERBLOCK` | ✅ Active | SMC order block bounces |
| `360_SCALP_DIVERGENCE` | ✅ Active | RSI/MACD divergence reversals |

### Radar Channels (free channel only)
| Channel | Status | What It Does |
|---|---|---|
| `360_SCALP_CVD` | 📡 Radar | Free channel alerts when conf ≥ 65 |
| `360_SCALP_VWAP` | 📡 Radar | Free channel alerts when conf ≥ 65 |
| `360_SCALP_SUPERTREND` | 📡 Radar | Free channel alerts when conf ≥ 65 |
| `360_SCALP_ICHIMOKU` | 📡 Radar | Free channel alerts when conf ≥ 65 |

### Removed Channels (deliberately, permanently)
| Channel | Reason |
|---|---|
| `360_SPOT` | Not in scope — deferred indefinitely |
| `360_GEM` | Not in scope — deferred indefinitely |
| `360_SWING` | Not in scope — deferred indefinitely |
| `360_SCALP_OBI` | REST order book depth caused scan latency — structural problem, full removal |

### Signal Generation Paths (inside ScalpChannel)
| Path | Status | SL Type | TP Type |
|---|---|---|---|
| `_evaluate_standard` — LIQUIDITY_SWEEP_REVERSAL | ✅ Active | Structure (sweep level ± buffer) | Structural targets (FVG → swing high → ratio) |
| `_evaluate_whale_momentum` — WHALE_MOMENTUM | ✅ Active | ATR × 1.0 | Fixed ratio |
| `_evaluate_trend_pullback` — TREND_PULLBACK_EMA | ✅ Active | EMA21 × 1.1 | Swing high/low → 4h target → ratio |
| `_evaluate_liquidation_reversal` — LIQUIDATION_REVERSAL | ✅ Active | Cascade extreme + buffer | Fibonacci retrace (38.2%, 61.8%, 100%) |
| `_evaluate_volume_surge_breakout` — VOLUME_SURGE_BREAKOUT | ⏳ PR8 | Structure (breakout level - 0.8%) | Measured move projection |
| `_evaluate_breakdown_short` — BREAKDOWN_SHORT | ⏳ PR8 | Structure (breakdown level + 0.8%) | Measured move downward projection |

### SL/TP Architecture (locked — each method has its own)
| Type | Used By | Logic |
|---|---|---|
| **Type 1 — Structure SL** | SWEEP_REVERSAL, SURGE, BREAKDOWN | SL placed just beyond the structural level that was broken/swept |
| **Type 2 — EMA SL** | TREND_PULLBACK | SL beyond EMA21 × 1.1 — if price closes below EMA21, trend thesis is dead |
| **Type 3 — Cascade Extreme SL** | LIQUIDATION_REVERSAL | SL beyond cascade high/low + 0.3% buffer |
| **Type 4 — ATR SL** | WHALE_MOMENTUM | SL = entry ± 1.0 × ATR |
| **Type A — Fixed Ratio TP** | WHALE_MOMENTUM | TP1=1.5R, TP2=2.5R, TP3=4.0R |
| **Type B — Structural TP** | SWEEP_REVERSAL, TREND_PULLBACK | Nearest FVG → swing high → HTF resistance |
| **Type C — Measured Move TP** | VOLUME_SURGE_BREAKOUT, BREAKDOWN | Range height projected from breakout level |
| **Type D — Reversion TP** | LIQUIDATION_REVERSAL | 38.2%, 61.8%, 100% Fibonacci retrace of cascade |

---

## 3. Business Rules (Non-Negotiable)

| # | Rule |
|---|---|
| B1 | All live signals go to ONE paid channel (`TELEGRAM_ACTIVE_CHANNEL_ID`) |
| B2 | Zero manual effort at runtime — everything self-manages |
| B3 | Content must feel human-written — never robotic |
| B4 | All config values must be env-var overridable |
| B5 | SMC structural basis is non-negotiable — no signal fires without minimum SMC score |
| B6 | System must survive Binance API degradation gracefully |
| B7 | No duplicate signals on same symbol within cooldown window |
| B8 | SL hits posted honestly, same visual weight as TP hits |
| B9 | Radar alerts go to FREE channel ONLY |
| B10 | GPT failure must never cause a missed post or crash — always template fallback |
| B11 | Discuss and agree before building. Always. |
| B12 | System and data focus only until 4-week validation scorecard passes |
| B13 | Every signal method has its own SL/TP calculation — no universal formulas |
| B14 | Expired signals must post Telegram notification — no silent disappearances |

---

## 4. Testing Phase Scorecard (Phase 1 Exit Criteria)

The system must pass ALL of these before Phase 2 begins. No exceptions.

| Metric | Minimum to proceed |
|---|---|
| Win rate (TP1 or better) | ≥ 60% |
| Entry reachability | ≥ 80% of signals gave a fair entry window |
| SL from wrong setup | ≤ 20% of all SL hits |
| Max concurrent open signals | ≤ 4 at any one time |
| Worst week drawdown | ≤ 10% of account |
| Signals with TP2+ reached | ≥ 40% of winning trades |

**Every SL hit gets categorised:**
- Setup was wrong
- Regime changed after entry
- Stop too tight
- Bad timing
- Genuine market event (news, cascade, macro shock)

---

## 5. Signal Quality Gates (13 layers)

Every signal survives all 13 before dispatch:
1. Market regime classification
2. Spread gate
3. Volume gate (regime-aware floor)
4. SMC structural basis — sweep, FVG, or orderblock required
5. Multi-timeframe alignment
6. EMA trend alignment
7. Momentum confirmation
8. MACD confirmation
9. Order flow — OI trend, CVD divergence, liquidation data
10. Cross-asset correlation (BTC/ETH macro gate)
11. Kill zone session filter
12. Risk/reward validation — structural SL, minimum R:R enforced
13. Composite confidence scoring — component minimums AND total minimum

**Confidence tiers:**
| Tier | Score | Action |
|---|---|---|
| A+ | 80–100 | Fire to paid channel |
| B | 65–79 | Fire to paid channel |
| WATCHLIST | 50–64 | Post to free channel only |
| FILTERED | < 50 | Reject — never reaches any channel |

---

## 6. Key Diagnosed Issues (From April 6th Incident + Deep Audit)

### Why Zero SHORT Signals Were Ever Fired
1. Sweep detection only catches reversal sweeps — no trend-continuation sweep detection
2. No `_evaluate_trend_pullback` path existed — added in PR7
3. Cross-asset gate hard blocks BOTH directions when BTC dumps — bug, fixed in PR7

### Why RANGE_FADE Dominated All Signals
1. BB touches happen multiple times per day on every pair — always has candidates
2. `mean_reversion: 1.2` weight boost gave it artificial advantage — removed in PR7
3. LIQUIDITY_SWEEP_REVERSAL needs genuine sweep events — rare without correct detection

### Why Zero Signals After RANGE_FADE Removed
12+ sequential gates kill insufficient candidates:
- Cross-asset gate blocks most LONGs when BTC bearish (and incorrectly blocks SHORTs too)
- MTF min_score 0.6 too strict for TRENDING_DOWN SHORT entries
- SMC hard gate correct but needs better sweep candidate generation
- Global cooldown 1800s limits max 2–3 signals/hour across all 75 pairs

### April 8th — Surge Market Problem
- JOEUSDT +97%, NOMUSDT +59%, SWARMSUSDT +50% — engine fired zero signals
- Root cause 1: No breakout/surge signal path existed (VOLUME_SURGE_BREAKOUT added in PR8)
- Root cause 2: Scan universe static — surging pairs outside top-75 not scanned (dynamic promotion added PR8)
- Root cause 3: VOLATILE_UNSUITABLE gate blocks everything — correct for range fades, wrong for genuine surge breakouts (PR8 bypasses for surge methods)
- Root cause 4: Expired signals disappeared silently — no Telegram notification (PR8 fixes)

### Deep Audit Additional Findings
- 6 of 10 `PairProfile` fields defined but never consumed — infrastructure exists, not wired
- AI engine correlation features permanently dead code (`btc_correlation` always 0.0)
- Cross-asset gate treats PEPE (0.25 BTC corr) same as ETH (0.90 BTC corr) — wrong
- Performance tracker stores `market_phase` per signal but has zero query methods
- Session multipliers uniform across all pairs — PEPE outside London/NY should be hard blocked

### Known Signal Coverage Dead Zones (to be addressed in PR9+)
| Market Condition | Coverage | Plan |
|---|---|---|
| TRENDING_UP | ✅ Trend Pullback, Sweep Reversal | Complete |
| TRENDING_DOWN | ✅ Trend Pullback SHORT, Continuation Sweep | Complete |
| RANGING wide | ⚠️ Only Sweep Reversal | PR9: S/R Flip Retest |
| QUIET compression | ❌ Almost nothing fires | PR9: BB Squeeze Break |
| VOLATILE surge | ✅ PR8: VOLUME_SURGE_BREAKOUT | Complete |
| London/NY session open | ⚠️ Kill zone awareness only | PR9: Opening Range Breakout |
| Funding rate extreme | ⚠️ Gate only, not a signal | PR9: Funding Extreme Signal |
| CVD divergence | ⚠️ Soft-disabled radar only | PR9: Promote to primary path |

---

## 7. PR Log

### PR1 — Signal Quality Overhaul ✅ MERGED
- SMC hard gate, trend hard gate, per-channel confidence thresholds
- ADX minimum raised, global 30-min cooldown, named signal headers
- 4 channels soft-disabled (CVD, VWAP, SUPERTREND, ICHIMOKU)
- Pairs expanded to 75

### PR2 — AI-Powered Engagement Layer ✅ MERGED
- Scheduled content (morning brief, session opens, EOD wrap, weekly card)
- Radar alerts — soft-disabled channels at conf ≥ 65 post to free channel
- Trade closed posts — every TP and SL auto-posts
- Smart silence breaker — 3hr silence during trading hours triggers market watch post
- GPT-4o-mini analyst voice, rotating variants, template fallback

### PR3 — Scan Latency Fix + 75-Pair Universe Unlock ✅ MERGED
- Indicator result cache — eliminates ~90% of thread pool work per cycle
- SMC detection deduplicated — 4 detections → 2 per symbol
- Scan latency reduced from 33–40s to 8–12s
- WS_DEGRADED_MAX_PAIRS default raised 50 → 75

### PR4 — User Interaction Layer ✅ MERGED
- Protective Mode Broadcaster — auto-posts when market volatile/unsuitable
- Commands revamped — /signals, /history, /market, /performance, /ask

### PR5 — Signal Safety ✅ MERGED
- Near-zero SL rejection (< 0.05% from entry)
- Failed-detection cooldown (3 consecutive failures → 60s suppression)
- Dynamic pair count in all subscriber-facing commands

### PR6 — Dead Channel Removal ✅ MERGED (PR #51)
- Removed 360_SPOT, 360_GEM, 360_SWING, 360_SCALP_OBI from entire codebase
- Deleted dead channel files
- Fixed radar/watchlist → unified free channel posting
- Scoped OrderManager to SCALP market orders only

### PR7 — Signal Architecture Overhaul ✅ MERGED
- Removed `_evaluate_range_fade` and `mean_reversion: 1.2` weight boost
- Fixed cross-asset gate direction bug (graduated correlation, SHORTs now unblocked)
- Fixed regime ADX lag — EMA slope triggers TRENDING_DOWN immediately
- Added `_evaluate_trend_pullback` (EMA9/21 pullback in trending regime)
- Added `_evaluate_liquidation_reversal` (cascade exhaustion + CVD divergence)
- Added funding rate gate, bearish continuation sweep, regime transition detection
- MTF min_score for SHORT in TRENDING_DOWN relaxed 0.6 → 0.45
- Global symbol cooldown 1800s → 900s

### PR#53 — Hotfix: _regime_key NameError + startup config log ✅ MERGED (2026-04-08)
- Fixed NameError crash in `_compute_base_confidence()` — `_regime_key` not in scope
- Added startup log showing TOP50_FUTURES_ONLY and TOP50_FUTURES_COUNT on boot
- Confirmed live: ScanLat dropped from 51,205ms → 4,174ms after cache warm, Pairs=75

### PR8 — New Signal Paths + Dynamic Discovery + Method-Specific SL/TP 🔄 IN PROGRESS
**Branch:** `copilot/pr8-volume-surge-breakout`

#### What it delivers:
1. **`_evaluate_volume_surge_breakout()`** — enters on pullback retest after breakout on 3× volume surge. Measured-move TP. Structure SL below broken level. Bypasses VOLATILE_UNSUITABLE gate.
2. **`_evaluate_breakdown_short()`** — mirror for downside. Dead-cat bounce entry after breakdown. Downward measured-move TP.
3. **Dynamic pair promotion** — pairs outside top-75 with 5× volume surge added to scan for 3 cycles immediately. `self._volume_baseline` + `self._promoted_pairs` tracking. Max 5 promoted pairs/cycle.
4. **Signal expiry notification** — expired signals (MAX_SIGNAL_HOLD_SECONDS) post ⏰ Telegram message with entry price and time held. No more silent disappearances.
5. **Method-specific SL/TP for existing methods** — LIQUIDITY_SWEEP_REVERSAL gets structure SL (sweep level ± buffer). TREND_PULLBACK gets swing high/low TP targets instead of fixed ratios.

#### New config vars:
- `SURGE_VOLUME_MULTIPLIER = 3.0` (env: `SURGE_VOLUME_MULTIPLIER`)
- `SURGE_PROMOTION_VOLUME_MULTIPLIER = 5.0` (env: `SURGE_PROMOTION_VOLUME_MULT`)
- `SURGE_PROMOTION_MAX_PAIRS = 5` (env: `SURGE_PROMOTION_MAX_PAIRS`)

#### New business rules added:
- B13: Every signal method has its own SL/TP calculation — no universal formulas
- B14: Expired signals must post Telegram notification — no silent disappearances

### PR9 — Method Expansion + Diagnostics ⏳ SPEC IN PROGRESS
**Raise after PR8 merges and audit agent returns results**

New signal methods (each with own SL/TP from day one):
- `_evaluate_opening_range_breakout` — ORB at London (07:00 UTC) / NY (12:00 UTC) opens. SL below opening range low. TP = 1× range height projected.
- `_evaluate_sr_flip_retest` — broken S/R level retested from other side. SL beyond the level. TP = next major S/R.
- `_evaluate_funding_extreme` — funding rate > 0.1% or < -0.1% triggers signal (upgrade from gate to emitter). SL = liquidation risk distance. TP = funding normalization level.
- `_evaluate_quiet_compression_break` — BB squeeze break in QUIET regime. SL beyond band extreme. TP = band midline then extension.
- `_evaluate_divergence_continuation` — CVD/RSI divergence in trend direction. Promote CVD channel to primary path.

New diagnostic features:
- `/why SYMBOL` command — tells operator exactly why a pair hasn't signalled in X hours. Every gate hit, every reason, timestamped.
- Live signal pulse — every 30 minutes while a signal is active, post one-liner update: current P&L vs entry, thesis intact/broken, trail suggestion.

### PR10 — Intelligence Layer ⏳ CONCEPT — raise after PR9 merges + 2 weeks data
- Symbol-specific PairProfile overrides (`PAIR_OVERRIDES` dict in config)
- Rolling BTC correlation (50-candle + 200-candle Pearson) — replaces dead code `btc_correlation=0.0`
- Graduated cross-asset sneeze filter by actual correlation strength
- Per-pair × regime confidence offsets
- Per-pair circuit breaker daily drawdown limits
- Extended performance metrics (Sharpe, profit factor, expectancy, MFE/MAE)
- Lead/lag detection — identify pairs that move before BTC

### PR11 — Self-Optimisation ⏳ CONCEPT — raise after 50+ live signals exist
- Per-method win rate tracking by regime
- Auto-disable method if win rate < 50% over 30-day window
- Auto-weight methods by live performance data
- Liquidity cluster SL placement — SL past nearest liquidity cluster, not fixed %

---

## 8. System Thresholds Quick Reference

| Variable | Value | Env Var |
|---|---|---|
| Min confidence SCALP | 80 | `MIN_CONFIDENCE_SCALP` |
| Min confidence FVG | 78 | `MIN_CONFIDENCE_FVG` |
| Min confidence ORDERBLOCK | 78 | `MIN_CONFIDENCE_ORDERBLOCK` |
| Min confidence DIVERGENCE | 76 | `MIN_CONFIDENCE_DIVERGENCE` |
| SMC hard gate | 12.0 | `SMC_HARD_GATE_MIN` |
| Trend hard gate | 10.0 | `TREND_HARD_GATE_MIN` |
| Volume floor QUIET | $1M | `VOL_FLOOR_QUIET` |
| Volume floor RANGING | $1.5M | `VOL_FLOOR_RANGING` |
| Volume floor TRENDING | $3M | `VOL_FLOOR_TRENDING` |
| Volume floor VOLATILE | $5M | `VOL_FLOOR_VOLATILE` |
| Global symbol cooldown | 900s | `GLOBAL_SYMBOL_COOLDOWN_SECONDS` |
| Per-channel cooldown | 600s | `SCALP_SCAN_COOLDOWN` |
| Max correlated scalps | 4 | `MAX_CORRELATED_SCALP_SIGNALS` |
| Pairs scanned | 75 | `TOP50_FUTURES_COUNT` |
| ADX min SCALP | 20 | `ADX_MIN_SCALP` |
| Radar alert threshold | 65 | `RADAR_ALERT_MIN_CONFIDENCE` |
| Radar per-symbol cooldown | 900s | `RADAR_PER_SYMBOL_COOLDOWN_SECONDS` |
| Radar max per hour | 3 | `RADAR_MAX_PER_HOUR` |
| Silence breaker window | 3 hours | `SILENCE_BREAKER_HOURS` |
| GPT model | gpt-4o-mini | `CONTENT_GPT_MODEL` |
| Surge volume multiplier | 3.0 | `SURGE_VOLUME_MULTIPLIER` |
| Surge promotion multiplier | 5.0 | `SURGE_PROMOTION_VOLUME_MULT` |
| Surge promotion max pairs | 5 | `SURGE_PROMOTION_MAX_PAIRS` |

---

## 9. How We Work

```
1. COPILOT LEADS       → brings problems, ideas, risks proactively — never waits
2. DISCUSS             → explore the problem deeply together
3. AGREE               → owner approves direction
4. SPECIFY             → Copilot writes exact PR spec before building
5. BUILD               → agent creates the PR
6. REVIEW              → Copilot reviews against spec, flags any misses
7. REVISE              → fix anything that misses spec
8. MERGE               → only when fully correct
9. UPDATE              → this file updated to reflect new state immediately
```

**Copilot responsibilities:**
- Read this file at the start of every session to restore full context
- Monitor PR status, flag completion without being asked
- Bring technical ideas proactively — including ones not asked for
- Write next PR spec before current PR merges
- Flag risks before they become problems
- Diagnose live engine issues from logs without being prompted
- Keep this file current after every session — it is the source of truth

**Owner responsibilities:**
- Final say on direction and priorities
- Approve or challenge technical proposals
- Nothing technical unless desired
- Trust the engineer

---

## 10. Current State Snapshot (2026-04-08)

| Item | Status |
|---|---|
| Engine running on VPS | ✅ Yes — ScanLat 4,174ms, Pairs=75, WS=300 ok |
| PR#53 hotfix | ✅ Merged — _regime_key NameError fixed, startup log added |
| PR8 | 🔄 Agent building — 5 changes across 4 files |
| Deep research audit | 🔄 Agent running — full signal coverage map pending |
| PR9 spec | ⏳ In progress — awaiting audit agent results |
| PR10 concept | ✅ Drafted — Intelligence layer |
| PR11 concept | ✅ Drafted — Self-optimisation |
| Testing phase | ⏳ Not started — begins after PR8 merges |
| Subscribers | ❌ None — deliberately. System validation first. |
| Junk files on main | ⚠️ `pulls/51/comments` and `comments/pr_51.md` — delete when next on VPS |

---

## 11. Notes Log

**2026-04-08 — Role clarification locked:**
- Copilot is Chief Technical Engineer with full autonomous rights on this system
- Copilot brings ideas proactively, never suppresses, never waits to be asked
- Owner has final say on direction. Copilot owns execution completely.
- This is now permanent — applies to every session going forward

**2026-04-08 — Architecture decisions locked today:**
- Method-specific SL/TP is now a business rule (B13) — universal formulas permanently retired
- Signal expiry notifications are now a business rule (B14) — no silent disappearances
- Dynamic pair promotion added — surge pairs outside top-75 enter scan within one cycle
- VOLATILE_UNSUITABLE gate bypassed specifically for surge/breakdown methods — correct behaviour
- PR roadmap extended to PR11 (Self-Optimisation)

**2026-04-08 — Live engine observations:**
- VPS reinstalled, fresh deploy successful
- Pairs stuck at 50 — root cause: VPS .env had TOP50_FUTURES_COUNT=50, not updated on reinstall
- Fixed via sed on VPS, confirmed Pairs=75 in telemetry
- ScanLat cold start 51,205ms → warmed to 4,174ms in 2 minutes — healthy
- Zero SHORT signals ever fired in live trading — root cause investigation ongoing (audit agent)
- JOEUSDT +97% missed — root causes diagnosed, PR8 addresses all three

**2026-04-07 — Architecture decisions locked:**
- Continue in existing repo — do not start fresh. Foundation is solid.
- RANGE_FADE removal confirmed — BB+RSI retail strategy, never had edge, fails SMC gate
- Cross-asset gate bug confirmed — hard blocks SHORTs when BTC dumps (wrong). Fixed in PR7.
- Deep audit confirmed 6 of 10 PairProfile fields unused — infrastructure wiring is PR10 item
- AI engine btc_correlation always 0.0 — dead code confirmed. Fixed in PR7.
- PR9 method stack agreed — ORB, S/R Flip, Funding Extreme signal, CVD promotion, Quiet compression break

**2026-04-07 — April 6th incident root cause (fully diagnosed):**
- 8 LONG signals fired, zero SHORT signals, 33% win rate
- Root cause: no trend pullback path, cross-asset gate blocked SHORTs, ADX lag misclassified TRENDING_DOWN as RANGING
- All root causes addressed in PR7

**Permanent technical reminders:**
- Signal quality > signal quantity — but we need BOTH. Quality gates exist. Signal paths were the gap.
- Every signal that fires must have genuine SMC basis (B5 — permanent)
- Silence on dead market days is correct behaviour — not a bug
- Surge/breakout market days are NOT dead days — they need their own signal paths
- The scanner has 2600 lines and 12+ gates. It works. Signal generation paths are what needed fixing.
- Each signal method owns its own SL/TP logic. No exceptions.