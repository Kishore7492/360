# 360 Crypto Eye — Owner Brief

> **This file is the single source of truth for business context, architecture decisions, and active priorities.**
> 
> At the start of every new Copilot session, paste this prompt:
> ```
> Read OWNER_BRIEF.md in mkmk749278/360-v2 — this is my crypto signal business.
> Continue from where we left off. Today I want to: [what you need]
> ```

---

## 1. What This Business Is

**360 Crypto Eye** is a paid crypto signal service built on a self-hosted, fully automated trading signal engine (`360-v2`). The engine scans Binance USDT-M futures in real time, detects Smart Money Concepts (SMC) setups, scores them through a multi-layer confidence pipeline, and posts actionable trade signals to a Telegram channel.

**Revenue model:** Monthly subscription. Subscribers pay to receive trade signals via Telegram. Retention depends on:
1. Signal quality — subscribers must be able to make money following signals
2. Channel activity — channel must feel alive and professionally run, never silent
3. Trust — every signal and post must look like a human expert analyst wrote it, not a bot

**The system is fully automated.** No manual effort at runtime. All content (signals, market commentary, session briefs, radar alerts) is AI-generated but feels human-written.

**Status:** In testing. No subscribers yet. Building the full system before launch.

**Owner:** mkmk749278
**Repo:** https://github.com/mkmk749278/360-v2
**Stack:** Python 3.11+, asyncio, aiohttp, Redis, Docker Compose, Telegram Bot API
**Deployment:** Single VPS, Docker Compose, GitHub Actions CD on push to `main`

---

## 2. Business Rules (Non-Negotiable)

These decisions are made and locked. Do not reverse without explicit owner instruction.

| # | Rule | Reason |
|---|---|---|
| B1 | All live signals go to ONE paid Telegram channel (`TELEGRAM_ACTIVE_CHANNEL_ID`) | Simplicity. Subscribers see everything in one place. |
| B2 | Zero manual effort at runtime | Owner is not monitoring 24/7. Everything must self-manage. |
| B3 | Content must feel human-written | AI-generated but natural language, named setups, real context. Never "Signal fired: conf=83.2" |
| B4 | No channel code deleted — only disabled via config | Instant re-enable via `.env`. No irreversible changes. |
| B5 | All config values must be env-var overridable | Owner tunes values without code changes or redeployment |
| B6 | SMC structural basis is non-negotiable | No signal fires without minimum SMC score — no pure momentum plays |
| B7 | System must survive Binance API degradation gracefully | Circuit breakers, fallbacks, no scan-blocking |
| B8 | No duplicate signals on same symbol within 30 minutes | Global cross-channel per-symbol cooldown enforced |
| B9 | Simple. Minimalistic. Eye-catching. | Every message looks clean, not robotic. Less is more. |
| B10 | SL hits posted honestly, same weight as TP hits | Transparency is a competitive advantage. Never go silent after a loss. |
| B11 | Radar alerts go to FREE channel ONLY | Paid channel gets live signals only. Free channel is the funnel. |
| B12 | GPT failure must never cause missed post or crash | Always fall back to template. Engine stability is sacred. |

---

## 3. Architecture Decisions (Already Made)

| Decision | What We Chose | Why |
|---|---|---|
| Signal universe | Top-75 USDT-M futures | More coverage while staying high-liquidity |
| Active channels | 4 (SCALP, FVG, ORDERBLOCK, DIVERGENCE) | Focused, non-overlapping |
| Soft-disabled channels | 4 (CVD, VWAP, SUPERTREND, ICHIMOKU) | Kept in code, repurposed as radar generators |
| Volume floor | Regime-aware | $1M QUIET → $5M VOLATILE |
| Confidence thresholds | Per-channel | SCALP=80, FVG=78, ORDERBLOCK=78, DIVERGENCE=76 |
| Kill zone POST_NY_LULL | Penalty only (0.65×), never hard block | Channel stays alive 20:00–24:00 UTC |
| Signal headers | Named setup type | "⚡ FVG RETEST" not "360_SCALP_FVG" |
| Global symbol cooldown | 1800s (30 min) cross-channel | No 3× BTC LONG in 10 minutes |
| SMC hard gate | smc_score ≥ 12.0 | Structural basis non-negotiable |
| Trend hard gate | trend_score ≥ 10.0 on scalp channels | Opposing EMAs = no signal |
| ADX minimum | 20 SCALP / 18 FVG | Was 15 — too loose |
| Message formatting | Minimalist, rotating variants, context-driven | Never looks identical twice |
| GPT model | gpt-4o-mini | Cost-efficient, fast, good quality for short posts |
| Radar threshold | 65 confidence / 70 for "watching closely" | Two tiers within radar |
| Signal volume target | 10–20 signals/day | Active but not noisy |
| EOD wrap time | 21:00 UTC | Covers London close, good for most timezones |

---

## 4. Message Formatting Design (Locked)

**Design rules — apply to every single message:**

1. Maximum 10 lines per message
2. One emoji maximum, always at the start
3. Numbers aligned vertically using spaces
4. One separator style only — the `·` dot
5. No labels that shout — `TP1` not `🎯 TARGET 1:`
6. Confidence bar only on live signals — `████████░░`
7. SL posts same visual weight as TP posts
8. GPT writes commentary only — numbers always from engine data
9. Variant selection is context-driven — urgency, time of day, recent post frequency
10. Template fallback is production-quality — good enough to post without GPT

**Content type visual identities:**

| Type | Style |
|---|---|
| Live Signal | Columns, conf bar, setup emoji, 3 rotating variants |
| Radar Alert | Flowing text, analyst voice, 6 rotating variants |
| Trade Closed | Clean fields, honest, running W/L record |
| Morning Brief | 2–3 lines GPT + pairs, clean header |
| Session Open | 2 lines max, no frame, immediate feel |
| Market Watch | Short, patience tone, 3 variants |
| Weekly Card | Stats table, clean columns |

---

## 5. PR Log

### PR1 — Signal Quality Overhaul ✅ MERGED
**PR:** [#44](https://github.com/mkmk749278/360-v2/pull/44) — merged 2026-04-06

- ✅ Regime-aware volume floor
- ✅ SMC hard gate (smc_score ≥ 12)
- ✅ Trend hard gate (trend_score ≥ 10 on scalp)
- ✅ Per-channel confidence thresholds
- ✅ ADX minimum raised
- ✅ Global 30-min cross-channel symbol cooldown
- ✅ Named signal headers
- ✅ 4 channels soft-disabled
- ✅ Pairs expanded to 75
- ✅ POST_NY_LULL no longer hard-blocks
- ✅ MAX_CORRELATED_SCALP_SIGNALS = 4

---

### PR2 — AI-Powered Engagement Layer 🔄 BUILDING
**Status:** Copilot agent building now

**5 pillars:**

1. **Scheduled daily content** — Morning brief (07:00), London open (08:00), NY open (13:30), EOD wrap (21:00), Weekly card (Mon 09:00) — both channels
2. **Radar alerts** — 4 soft-disabled channels run at conf ≥ 65, post to FREE channel only. 6 dynamic variants. Max 3/hour.
3. **Trade closed posts** — Every TP and SL hits auto-post to active channel. Honest. Running W/L record.
4. **Smart silence breaker** — No post for 3 hours during 08:00–22:00 UTC → auto market watch post
5. **Dynamic presentation** — 2–6 variants per content type, GPT-4o-mini persona, emoji pools, length variation, template fallback

**New modules:**
- `src/content_engine.py` — GPT wrapper + template renderer
- `src/formatter.py` — all message formatting and variants
- `src/scheduler.py` — asyncio cron
- `src/radar_channel.py` — radar evaluator
- `src/prompts/` — all GPT prompt templates

---

### PR3 — Revenue & Subscriber Features ⏳ PLANNED
- Subscriber tier system
- Auto-generated weekly performance image
- `/mystats`, `/history`, `/active` commands
- Referral tracking

---

## 6. Current Priorities

1. ✅ PR1 merged
2. 🔄 PR2 building
3. ⏳ Monitor signal volume (target 10–20/day)
4. ⏳ PR2 review and merge
5. ⏳ PR3 revenue features

---

## 7. System Thresholds Quick Reference

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
| Global symbol cooldown | 1800s | `GLOBAL_SYMBOL_COOLDOWN_SECONDS` |
| Per-channel cooldown | 600s | `SCALP_SCAN_COOLDOWN` |
| Max correlated scalps | 4 | `MAX_CORRELATED_SCALP_SIGNALS` |
| Pairs scanned | 75 | `TOP50_FUTURES_COUNT` |
| ADX min SCALP | 20 | `ADX_MIN_SCALP` |
| ADX min FVG | 18 | `ADX_MIN_FVG` |
| Radar alert threshold | 65 | `RADAR_ALERT_MIN_CONFIDENCE` |
| Radar watching closely | 70 | `RADAR_ALERT_WATCHING_CLOSELY_CONFIDENCE` |
| Radar per-symbol cooldown | 900s | `RADAR_PER_SYMBOL_COOLDOWN_SECONDS` |
| Radar max per hour | 3 | `RADAR_MAX_PER_HOUR` |
| Silence breaker window | 3 hours | `SILENCE_BREAKER_HOURS` |
| GPT model | gpt-4o-mini | `CONTENT_GPT_MODEL` |

---

## 8. Active Channels

| Channel | Status | Purpose |
|---|---|---|
| `360_SCALP` | ✅ Active | Sweep reversals, range fades, whale momentum |
| `360_SCALP_FVG` | ✅ Active | Fair Value Gap retests |
| `360_SCALP_ORDERBLOCK` | ✅ Active | SMC order block bounces |
| `360_SCALP_DIVERGENCE` | ✅ Active | RSI/MACD divergence reversals |
| `360_SCALP_CVD` | 📡 Radar only | Free channel radar alerts |
| `360_SCALP_VWAP` | 📡 Radar only | Free channel radar alerts |
| `360_SCALP_SUPERTREND` | 📡 Radar only | Free channel radar alerts |
| `360_SCALP_ICHIMOKU` | 📡 Radar only | Free channel radar alerts |

---

## 9. How to Continue a Session

```
Read OWNER_BRIEF.md in mkmk749278/360-v2 — this is my crypto signal business.
Continue from where we left off. Today I want to: [what you need]
```

---

## 10. Partner Notes (Locked Decisions)

- Signal quality > signal quantity. 10 clean signals beats 30 noisy ones.
- The free channel is a sales funnel. Every free post makes someone want to upgrade.
- The channel must never go silent. Silence breaker is non-negotiable.
- Every loss gets posted honestly. Transparency retains subscribers long-term.
- Simple. Minimalistic. Eye-catching. No walls of text. No robot formatting.
- GPT writes the voice, engine provides the numbers. Never invent data.
- The system must feel like a professional analyst is watching 24/7. That is the product.
- We build the business, not just fix bugs. Every PR moves the business forward.