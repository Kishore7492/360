# PR-7A: Family-aware scoring correction

## What changed

PR-7A applies a narrow scoring-architecture correction without changing global thresholds or routing doctrine.

### 1) Regime-affinity coverage corrected (`src/signal_quality.py`)
- Added missing affinity entries for active paths where architecturally justified:
  - `TREND_PULLBACK_EMA`
  - `SR_FLIP_RETEST`
  - `FAILED_AUCTION_RECLAIM`
  - `POST_DISPLACEMENT_CONTINUATION`
  - `CONTINUATION_LIQUIDITY_SWEEP` in `VOLATILE`
- Tier thresholds remain unchanged (A+ 80+, B 65–79, WATCHLIST 50–64).

### 2) Family thesis scoring expanded (`SignalScoringEngine`)
- Retained shared base model.
- Added bounded family-aware thesis treatment for previously under-credited families:
  - reclaim/retest (`SR_FLIP_RETEST`, `FAILED_AUCTION_RECLAIM`)
  - trend-pullback (`TREND_PULLBACK_EMA`)
  - breakout/displacement (`VOLUME_SURGE_BREAKOUT`, `POST_DISPLACEMENT_CONTINUATION`)
- Existing family-aware paths (reversal/order-flow/sweep-continuation) are preserved.

### 3) Runtime scoring telemetry expanded (`src/scanner/__init__.py`)
- Added rolling counters for **pre-penalty** and **post-penalty** score distribution by:
  - channel
  - setup family
  - setup class/path
- Telemetry now records both:
  - score bands (`00-09`, `10-19`, ..., `90-99`, `100`)
  - tier buckets (`A+`, `B`, `WATCHLIST`, `FILTERED`)

## How to validate PR-7A at runtime

1. Inspect scanner logs every 100 cycles for:
   - `Scoring pre/post distribution (last 100 cycles): {...}`
2. Focus on targeted active paths:
   - `SR_FLIP_RETEST`
   - `FAILED_AUCTION_RECLAIM`
   - `TREND_PULLBACK_EMA`
   - `CONTINUATION_LIQUIDITY_SWEEP`
   - `LIQUIDITY_SWEEP_REVERSAL`
   - `VOLUME_SURGE_BREAKOUT`
   - `POST_DISPLACEMENT_CONTINUATION`
3. Compare:
   - `pre_penalty:tier:*` vs `post_penalty:tier:*`
   - shift from `WATCHLIST` toward `B` for valid families
4. Confirm no doctrine drift:
   - thresholds unchanged
   - router/WATCHLIST policy unchanged
   - penalties unchanged (PR-7B scope)
