# Runtime Truth Report

## Executive summary
- Overall health/freshness: **stale**
- Top anomalies/concerns: EVAL::WHALE_MOMENTUM, EVAL::VOLUME_SURGE_BREAKOUT, EVAL::OPENING_RANGE_BREAKOUT
- Top promising signals/paths: none
- Recommended next investigation target: **EVAL::WHALE_MOMENTUM**

## Runtime health
- Engine running: `True` (status=running, health=healthy)
- Heartbeat age: `0` sec (warning=False)
- Latest performance record age: `None` sec

## Path funnel truth
| Path/Setup | Attempts | No-signal | Generated | Scanner prep | Gated | Emitted | Classification |
|---|---:|---:|---:|---:|---:|---:|---|
| BREAKDOWN_SHORT | 0 | 0 | 1 | 1 | 1 | 0 | low-sample (none) |
| CONTINUATION_LIQUIDITY_SWEEP | 0 | 0 | 15 | 15 | 12 | 1 | low-sample (none) |
| EVAL::BREAKDOWN_SHORT | 66122 | 66121 | 1 | 0 | 0 | 0 | low-sample (regime_blocked) |
| EVAL::CONTINUATION_LIQUIDITY_SWEEP | 66122 | 66107 | 15 | 0 | 0 | 0 | low-sample (regime_blocked) |
| EVAL::DIVERGENCE_CONTINUATION | 66122 | 66122 | 0 | 0 | 0 | 0 | non-generating (regime_blocked) |
| EVAL::FAILED_AUCTION_RECLAIM | 66122 | 54839 | 11283 | 0 | 0 | 0 | low-sample (basic_filters_failed) |
| EVAL::FUNDING_EXTREME | 66122 | 66122 | 0 | 0 | 0 | 0 | dependency-missing (none) |
| EVAL::LIQUIDATION_REVERSAL | 66122 | 66122 | 0 | 0 | 0 | 0 | dependency-missing (cascade_threshold_not_met) |
| EVAL::OPENING_RANGE_BREAKOUT | 66122 | 66122 | 0 | 0 | 0 | 0 | non-generating (regime_blocked) |
| EVAL::POST_DISPLACEMENT_CONTINUATION | 66122 | 66121 | 1 | 0 | 0 | 0 | low-sample (regime_blocked) |
| EVAL::QUIET_COMPRESSION_BREAK | 66122 | 65979 | 143 | 0 | 0 | 0 | low-sample (none) |
| EVAL::SR_FLIP_RETEST | 66122 | 63606 | 2516 | 0 | 0 | 0 | low-sample (flip_close_not_confirmed) |
| EVAL::STANDARD | 66122 | 64265 | 1857 | 0 | 0 | 0 | low-sample (none) |
| EVAL::TREND_PULLBACK | 66122 | 66114 | 8 | 0 | 0 | 0 | low-sample (regime_blocked) |
| EVAL::VOLUME_SURGE_BREAKOUT | 66122 | 66122 | 0 | 0 | 0 | 0 | non-generating (regime_blocked) |
| EVAL::WHALE_MOMENTUM | 66122 | 66122 | 0 | 0 | 0 | 0 | non-generating (regime_blocked) |
| FAILED_AUCTION_RECLAIM | 0 | 0 | 11283 | 11283 | 11283 | 0 | low-sample (none) |
| LIQUIDITY_SWEEP_REVERSAL | 0 | 0 | 1857 | 1857 | 1575 | 2 | low-sample (none) |
| POST_DISPLACEMENT_CONTINUATION | 0 | 0 | 1 | 1 | 1 | 0 | low-sample (none) |
| QUIET_COMPRESSION_BREAK | 0 | 0 | 143 | 143 | 143 | 0 | low-sample (none) |
| SR_FLIP_RETEST | 0 | 0 | 2516 | 2516 | 2288 | 5 | low-sample (none) |
| TREND_PULLBACK_EMA | 0 | 0 | 8 | 8 | 6 | 0 | low-sample (none) |

## Evaluator no-signal reasons
- EVAL::BREAKDOWN_SHORT: regime_blocked=48521, volume_spike_missing=11583, basic_filters_failed=5159
- EVAL::CONTINUATION_LIQUIDITY_SWEEP: regime_blocked=65055, ema_alignment_reject=502, sweeps_not_detected=240
- EVAL::DIVERGENCE_CONTINUATION: regime_blocked=65055, cvd_divergence_failed=753, cvd_insufficient=268
- EVAL::FAILED_AUCTION_RECLAIM: basic_filters_failed=21119, auction_not_detected=14923, regime_blocked=10415
- EVAL::FUNDING_EXTREME: none=48521, funding_not_extreme=12065, basic_filters_failed=5140
- EVAL::LIQUIDATION_REVERSAL: cascade_threshold_not_met=41150, basic_filters_failed=23488, cvd_divergence_failed=1444
- EVAL::OPENING_RANGE_BREAKOUT: regime_blocked=66122
- EVAL::POST_DISPLACEMENT_CONTINUATION: regime_blocked=65055, ema_alignment_reject=502, breakout_not_found=328
- EVAL::QUIET_COMPRESSION_BREAK: none=65979
- EVAL::SR_FLIP_RETEST: flip_close_not_confirmed=25128, basic_filters_failed=20902, regime_blocked=10415
- EVAL::STANDARD: none=64265
- EVAL::TREND_PULLBACK: regime_blocked=65055, ema_alignment_reject=501, retest_proximity_failed=226
- EVAL::VOLUME_SURGE_BREAKOUT: regime_blocked=48521, volume_spike_missing=11530, basic_filters_failed=5159
- EVAL::WHALE_MOMENTUM: regime_blocked=48521, momentum_reject=17601

## Dependency readiness
- cvd: presence[present=66122] state[empty=23, populated=66099] buckets[few=1881, many=56520, none=23, some=7698] sources[none] quality[none]
- funding_rate: presence[present=66122] state[empty=509, populated=65613] buckets[few=65613, none=509] sources[none] quality[none]
- liquidation_clusters: presence[present=66122] state[empty=35969, populated=30153] buckets[few=23589, none=35969, some=6564] sources[none] quality[none]
- oi_snapshot: presence[present=66122] state[empty=502, populated=65620] buckets[few=5549, many=34375, none=502, some=25696] sources[none] quality[none]
- order_book: presence[absent=8976, present=57146] state[populated=57146, unavailable=8976] buckets[few=57146, none=8976] sources[book_ticker=57146, unavailable=8976] quality[none=8976, top_of_book_only=57146]
- orderblocks: presence[absent=66122] state[unavailable=66122] buckets[none=66122] sources[none] quality[none]
- recent_ticks: presence[present=66122] state[empty=2359, populated=63763] buckets[many=63763, none=2359] sources[none] quality[none]

## Lifecycle truth summary
- Median create→dispatch: `None` sec
- Median create→first breach: `None` sec
- Median create→terminal: `None` sec
- Median first breach→terminal: `None` sec
- Fast-failure buckets: `{"under_120s": {"count": 0, "pct": 0.0}, "under_180s": {"count": 0, "pct": 0.0}, "under_30s": {"count": 0, "pct": 0.0}, "under_60s": {"count": 0, "pct": 0.0}}`
- ~3 minute terminal-close behavior: `{"count": 0, "pct": 0.0}`

## Quality-by-path/setup summary
| Path/Setup | Emitted | Closed | Win rate | SL rate | TP rate | Avg PnL% | Median first breach (s) | Median terminal (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|

## Post-correction focus (target setups)
| Setup | Attempts | Generated | Emitted | Gated | Win rate | SL rate | Median first breach (s) | Median terminal (s) | Geometry preserved | Geometry changed | Geometry rejected |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SR_FLIP_RETEST | 0 | 2516 | 5 | 2288 | 0.0 | 0.0 | None | None | 228 | 0 | 0 |
| TREND_PULLBACK_EMA | 0 | 8 | 0 | 6 | 0.0 | 0.0 | None | None | 2 | 0 | 0 |

## Window-over-window comparison
- Path emissions Δ: `8`
- Gating Δ: `15309`
- No-generation Δ: `909884`
- Fast failures Δ: `0`
- Quality changes: `{}`
- Post-correction setup deltas: `{"SR_FLIP_RETEST": {"emitted_delta": 5, "geometry_changed_delta": 0, "geometry_preserved_delta": 228, "geometry_rejected_delta": 0, "median_first_breach_delta_sec": 0.0, "median_terminal_delta_sec": 0.0, "sl_rate_delta": 0.0, "win_rate_delta": 0.0}, "TREND_PULLBACK_EMA": {"emitted_delta": 0, "geometry_changed_delta": 0, "geometry_preserved_delta": 2, "geometry_rejected_delta": 0, "median_first_breach_delta_sec": 0.0, "median_terminal_delta_sec": 0.0, "sl_rate_delta": 0.0, "win_rate_delta": 0.0}}`

## Recommended operator focus
- Most suspicious degradation: **EVAL::WHALE_MOMENTUM**
- Most promising healthy path: **none**
- Most likely bottleneck: **FAILED_AUCTION_RECLAIM**
- Suggested next investigation target: **EVAL::WHALE_MOMENTUM**
