# Audit Note — 2026-04-13 — 360_SCALP Tier Dispatch Alignment

**Model:** claude-sonnet-4.6 (Copilot Coding Agent)
**PR:** copilot/implement-narrow-governance-correction-pr
**Date:** 2026-04-13
**Preceded by:** PR-14, PR-15, PR-16, PR-17 (all merged into main)

---

## Contradiction verified

Two independent architecture contradictions were confirmed by direct code inspection
before any changes were made.

### Contradiction 1 — B-tier dead zone

**Evidence:**
- `src/scanner/__init__.py:383-402` (`classify_signal_tier`): declares `B = 65–79`
- `config/__init__.py:579`: `CHANNEL_SCALP.min_confidence = 80`
- `src/scanner/__init__.py:2883-2883`: `min_conf = chan.config.min_confidence` → 80
- `src/scanner/__init__.py:2954-2967`: signals with `confidence < min_conf` are dropped

**Effect:** Every 360_SCALP candidate with confidence 65–79 was classified as B-tier
by `classify_signal_tier` and then immediately rejected by the scanner's min_conf gate.
The tier classification was correct; the floor was stale. Live monitor confirmed this
with repeated `score_65to79:LIQUIDITY_SWEEP_REVERSAL` counters producing zero output.

### Contradiction 2 — WATCHLIST downstream destruction

**Evidence:**
- `src/scanner/__init__.py:2942-2953`: scanner correctly early-returns WATCHLIST
  signals (50–64) for scalp channels without dropping them
- `src/signal_router.py:554-564`: router applies `signal.confidence < chan_cfg.min_confidence`
  unconditionally, which drops WATCHLIST signals (confidence 50–64) against a floor of 80

**Effect:** Scanner preserved WATCHLIST signals correctly; router silently destroyed them.
Policy said "WATCHLIST is kept"; downstream behavior said "WATCHLIST is dropped". The
semantics were contradictory across the scanner→router boundary.

---

## Chosen policy mapping (after fix)

| Tier       | Confidence range | 360_SCALP dispatch outcome |
|------------|-----------------|---------------------------|
| A+         | 80–100           | Dispatched to paid channel ✓ (unchanged) |
| B          | 65–79            | Dispatched to paid channel ✓ (fixed: was dead-zoned) |
| WATCHLIST  | 50–64            | Preserved through scanner AND router ✓ (fixed: router bypass added) |
| FILTERED   | < 50             | Dropped — unchanged |

All other channels retain their existing `min_confidence` values and dispatch behavior
unchanged. The fix is scoped exclusively to the 360_SCALP dispatcher alignment.

---

## Note on GPT-5.3-Codex execution plan

The execution plan referenced routing WATCHLIST signals to a "free/radar-style" downstream
route. Upon code inspection, no separate free-channel dispatch path exists for WATCHLIST
signals in the current router. The router sends all dispatched signals to the paid channel
(as mapped by `CHANNEL_TELEGRAM_MAP`). The fix implemented here removes the contradiction
(WATCHLIST signals are no longer silently destroyed) without forcing a radar-route assumption
that is not supported by current router architecture. WATCHLIST format differentiation
(e.g., zone-alert formatting) is a separate downstream concern and not part of this PR.

---

## Files changed

| File | Change |
|------|--------|
| `config/__init__.py` | `CHANNEL_SCALP.min_confidence` default lowered from 80 → 65 (B-tier boundary) via `MIN_CONFIDENCE_SCALP` env var default |
| `src/signal_router.py` | Added WATCHLIST bypass in channel min-confidence filter: signals tagged `signal_tier="WATCHLIST"` from `_SCALP_CHANNEL_NAMES` channels skip the router's `min_confidence` floor |

---

## Tests added

**File:** `tests/test_pr18_scalp_tier_dispatch_alignment.py`

| Test class | Coverage |
|-----------|---------|
| `TestClassifySignalTier` | Tier boundary assertions for A+/B/WATCHLIST/FILTERED — canonical policy is explicit and testable |
| `TestScalpMinConfidenceConfig` | `CHANNEL_SCALP.min_confidence == 65`, all B-tier confidences pass the floor, other scalp channels unchanged |
| `TestRouterWatchlistBypass` | WATCHLIST scalp signals are dispatched; non-WATCHLIST below floor still rejected; bypass scoped to `_SCALP_CHANNEL_NAMES` only |
| `TestAPlusBehaviorUnchanged` | A+ at 85 and at boundary 80 still dispatched — no regression |
| `TestBTierDispatch` | B-tier at boundary (65), mid-range (72) now dispatched; sub-65 non-WATCHLIST still rejected |

16 focused tests, all passing.

---

## What was not changed

- Spread gate thresholds
- MTF gate formula or weights
- SMC hard gate exemptions
- FVG SL geometry constraints
- Protective mode trigger logic
- QUIET_SCALP_MIN_CONFIDENCE (65.0 — already aligned; unchanged)
- Other scalp sub-channel min_confidence values (FVG=78, CVD=75, VWAP=75, etc.)
- Global scanner scoring logic
- Any non-scalp channel behavior

---

## Risk assessment

**Over-loosening risk:** Contained. Other structural gates (spread, MTF, trend, SMC,
component score minimums) remain in place. The fix only removes a stale floor that was
incorrectly blocking already-qualified candidates.

**Regression risk:** Low. Existing tests (test_signal_router.py, test_pr03_scalp_arbitration.py,
test_audit_findings.py) all pass. No changes to scoring logic.

**Business risk:** Previously live-qualified B-tier candidates will now be dispatched
as intended. This improves truthful signal output without weakening quality protections.
