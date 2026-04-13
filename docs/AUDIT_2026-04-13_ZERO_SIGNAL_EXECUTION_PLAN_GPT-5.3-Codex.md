# Zero-Signal Execution Plan — 2026-04-13 — GPT-5.3-Codex

## Scope and evidence base

This execution memo is based on:
- `origin/main:OWNER_BRIEF.md`
- `origin/main:docs/ACTIVE_CONTEXT.md`
- `origin/monitor-logs:monitor/latest.txt` (generated 2026-04-13 06:49:44 UTC)
- `docs/AUDIT_2026-04-13_ZERO_SIGNAL_DIAGNOSIS_GPT-5.4.md`
- Independent code verification in:
  - `src/scanner/__init__.py`
  - `config/__init__.py`
  - `src/signal_router.py`
  - `src/signal_quality.py`

---

## 1) Verified diagnosis summary

### What GPT-5.4 got right (confirmed now)

1. **Infrastructure is alive; zero output is suppression-funnel driven, not runtime failure.**  
   Confirmed by live monitor: healthy container, fresh heartbeat, WS healthy, no runtime exceptions, repeated full scan cycles with suppression summaries.

2. **Spread-quality suppression is genuinely dominant.**  
   Monitor repeatedly shows `pair_quality:spread too wide` in high counts (often ~32–60/cycle).

3. **Generic scanner MTF gate is a major suppressor on main path.**  
   Monitor repeatedly shows `mtf_gate:360_SCALP` (peaks around 14/cycle).  
   Code confirms a universal scanner-level `check_mtf_gate()` call in `_prepare_signal()` before later gates.

4. **`360_SCALP` B-tier dead-zone contradiction is real.**  
   Code confirms:
   - tier classification defines B as 65–79 (`classify_signal_tier`)  
   - `CHANNEL_SCALP.min_confidence = 80`  
   - final floor rejects `< min_conf` in scanner  
   - monitor shows repeated `score_65to79:LIQUIDITY_SWEEP_REVERSAL` and still zero signals.

5. **Quiet-regime block is actively filtering sub-65 scalp candidates.**  
   Monitor repeatedly logs `QUIET_SCALP_BLOCK ... conf < 65.0`; code confirms this gate for QUIET + scalp channels.

6. **Protective mode is not a direct signal-block gate.**  
   Code confirms protective mode uses suppression counts to broadcast state; it does not independently reject candidates.

### Corrections / refinements to GPT-5.4 prioritization

1. **Telemetry-first is no longer the strongest immediate move.**  
   Current telemetry is already sufficient to justify action on a confirmed architecture contradiction (B-tier dead zone).

2. **There is a second dispatch-policy contradiction beyond B-tier.**  
   Scanner explicitly preserves WATCHLIST (50–64) for scalp, but router applies channel min-confidence again (`signal.confidence < chan_cfg.min_confidence`) and drops them.  
   So WATCHLIST semantics are also not being truthfully expressed downstream.

3. **PR sequencing in `ACTIVE_CONTEXT` is now stale against confirmed live evidence.**  
   Keeping B-tier governance as a later gated item (PR-19) is no longer evidence-aligned.

### Classification of conclusions

- **Confirmed now (actionable):**
  - B-tier dead zone contradiction
  - WATCHLIST downstream contradiction
  - spread suppression dominance
  - heavy generic MTF suppression
  - quiet sub-65 suppression
- **Strongly likely; needs targeted validation while implementing:**
  - MTF gate is over-generic for some families (especially non-trend theses)
- **Still too speculative for immediate change:**
  - broad spread threshold loosening
  - broad quiet-floor loosening
  - broad volatile gate removal for auxiliary channels

---

## 2) Execution recommendation

### Single best next technical move

**Insert an immediate governance/dispatch-policy alignment PR for `360_SCALP` tiers (A+/B/WATCHLIST) before PR-18 and ahead of PR-16.**

Concretely: make downstream dispatch behavior match declared tier doctrine so valid B-tier and WATCHLIST outcomes are not structurally dropped by conflicting floors.

Why this is the strongest move now:
- Highest **evidence-to-impact** ratio (already proven in live logs + code)
- Lowest-risk path to improve **truthful output** without weakening spread/market safety
- Removes confirmed architecture contradiction instead of waiting on additional telemetry inertia

---

## 3) PR sequence recommendation

### Immediate next PR

1. **New PR (insert before PR-16): `360_SCALP Tier Dispatch Policy Alignment`**
   - Resolve B-tier dead zone immediately
   - Resolve WATCHLIST downstream contradiction
   - Keep spread/quality gates unchanged

### Next two PRs after that

2. **PR-16 (existing): WHALE_MOMENTUM QUIET regime block**
   - Keep, but lower priority than tier-dispatch contradiction because current monitor evidence is not whale-dominant.

3. **PR-18 (refined scope): Family-aware MTF dispatch policy for non-trend theses**
   - Proceed as targeted refinement after tier-policy alignment is merged and observed.

### Deferred / gated items

- Broad threshold loosening (spread, quiet, volatile)
- Portfolio-wide evaluator redesign
- Any major strategy reshuffle not tied to confirmed contradictions

### Items that should not be changed yet

- Pair-quality spread guardrails
- FVG hard geometry protection rules
- Protective mode broadcaster behavior
- Core SMC/trend gate doctrine globally (until family-scoped changes are specified)

### Direct answers to sequencing questions

- **Is PR-16 still the correct next PR?** **No.** It should follow a new tier-dispatch governance PR.
- **Should a new governance/dispatch-policy PR be inserted before PR-18?** **Yes.** Insert immediately.
- **Telemetry completion first or direct architecture correction now?** **Direct correction now** for tier contradiction; continue telemetry in parallel but not as blocker.

---

## 4) PR-ready spec (implementation-grade)

### Title

`PR-XX: Align 360_SCALP Tier Semantics With Actual Dispatch (A+/B/WATCHLIST)`

### Problem

Current code classifies signal quality tiers but downstream floors contradict those tiers:
- B-tier (65–79) is classified as valid but blocked by `min_confidence=80` for `360_SCALP`
- WATCHLIST (50–64) is preserved by scanner but dropped in router by channel min-confidence re-check

This creates an architecture mismatch: system detects qualified opportunities but cannot express them according to declared policy.

### Exact target behavior

1. `360_SCALP` A+ (80+) remains dispatchable to paid channel.
2. `360_SCALP` B (65–79) becomes dispatchable per strategy doctrine.
3. `360_SCALP` WATCHLIST (50–64) follows explicit watchlist route (free/radar-style) without being blocked by paid-channel min-confidence checks.
4. Non-`360_SCALP` channels keep existing confidence floors unless explicitly specified.
5. Suppression telemetry remains explicit and auditable by tier and reason.

### Why this is the right next move now

- Contradiction is already confirmed by code + live monitor (`score_65to79` present with zero output).
- Fix is narrow, policy-aligned, and does not require broad threshold loosening.
- It directly improves truthful expression while preserving risk discipline.

### Files likely involved

- `src/scanner/__init__.py` (tier/floor gating logic for `360_SCALP`)
- `src/signal_router.py` (router min-confidence behavior vs tiered/watchlist handling)
- `config/__init__.py` (if final policy requires explicit channel floor realignment)
- Tests:
  - `tests/test_scanner.py` and/or new focused tier-gating tests
  - `tests/test_signal_router.py` and/or new watchlist-routing tests
  - `tests/test_scoring_telemetry.py` update/extension if counter expectations change

### What must not change

- Spread gate thresholds
- MTF formula/weights (in this PR)
- SMC hard gate exemptions
- Trend hard gate exemptions
- FVG SL geometry constraints
- Protective mode trigger logic

### Tests required

Minimum required acceptance tests:
1. `360_SCALP` score 72 candidate is not rejected solely by legacy `min_confidence=80` path.
2. WATCHLIST (e.g., score 55) is routed according to explicit watchlist policy and not dropped by router min-confidence gate.
3. A+ path behavior unchanged.
4. Non-`360_SCALP` channel min-confidence behavior unchanged.
5. Suppression telemetry still records the correct reason buckets and tiers.

### Review standard

PR only passes if reviewers can trace an unambiguous tier-to-dispatch mapping in code and test coverage proves:
- no hidden fallback to legacy contradictory floors,
- no broad gate loosening,
- no silent behavior drift in unrelated channels.

---

## 5) Risk analysis

### Risk of over-loosening

If implemented as a blanket min-confidence reduction across all channels, signal quality could degrade quickly.  
**Mitigation:** scope strictly to `360_SCALP` tier-policy semantics; keep all other structural gates untouched.

### Risk of under-correcting

If only one layer is changed (scanner or router) contradiction may persist.  
**Mitigation:** treat scanner + router as one policy surface and test end-to-end dispatch behavior by tier.

### Conflict risk

Medium. Nearby roadmap items touch scanner gates and scoring behavior.  
**Mitigation:** keep this PR narrow (policy mapping only), avoid touching scoring formulas or MTF internals.

### Business risk

- **If not fixed now:** continued “engine alive but silent” degrades trust.
- **If fixed carelessly:** low-quality inflation risk.

Best business tradeoff is a narrow doctrine-alignment PR with explicit guardrails.

### Risk of following telemetry too long instead of acting

This risk is now high: contradiction is confirmed, not hypothetical. Waiting for more telemetry before acting creates avoidable delay and extends zero-signal state without improving truthfulness.

---

## Explicit answers to required technical questions

1. **Best evidence-to-impact fix:** `360_SCALP` tier dispatch policy alignment (B-tier + WATCHLIST contradiction fix).
2. **Lowest-risk truthful-output improvement:** same fix, scoped narrowly to policy mapping (not threshold loosening everywhere).
3. **Suppressions that appear correct and should remain:** spread-quality gate, quiet sub-65 block, FVG over-wide SL reject, protective mode broadcast.
4. **Suppressions that appear excessive/mismatched:** B-tier blocked by `min_conf=80`; WATCHLIST blocked by router min-confidence; likely over-generic scanner MTF gate (next PR, targeted).
5. **Is B-tier contradiction strong enough to elevate now?** Yes, definitively.
6. **Is PR-16 still correct next PR?** No; it should follow tier-policy correction.
7. **Insert governance/dispatch-policy PR before PR-18?** Yes.
8. **Telemetry next or architecture correction now?** Architecture correction now for confirmed contradiction; telemetry continues but not as blocker.
9. **Likely code locations for strongest next PR:** `src/scanner/__init__.py`, `src/signal_router.py`, optional `config/__init__.py`, focused tests in scanner/router suites.
10. **Regression risks:** accidental over-loosening, partial-layer fix leaving contradiction, unintended behavior drift in non-scalp channels.

