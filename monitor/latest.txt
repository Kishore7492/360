# Runtime Truth Report

## Executive summary
- Overall health/freshness: **stale**
- Top anomalies/concerns: EVAL::LIQUIDATION_REVERSAL, EVAL::WHALE_MOMENTUM, EVAL::VOLUME_SURGE_BREAKOUT
- Top promising signals/paths: none
- Recommended next investigation target: **EVAL::LIQUIDATION_REVERSAL**

## Runtime health
- Engine running: `True` (status=running, health=healthy)
- Heartbeat age: `9` sec (warning=False)
- Latest performance record age: `None` sec

## Path funnel truth
| Path/Setup | Attempts | No-signal | Generated | Scanner prep | Gated | Emitted | Classification |
|---|---:|---:|---:|---:|---:|---:|---|
| CONTINUATION_LIQUIDITY_SWEEP | 0 | 0 | 1680 | 1680 | 1604 | 13 | low-sample |
| EVAL::BREAKDOWN_SHORT | 430114 | 430114 | 0 | 0 | 0 | 0 | non-generating |
| EVAL::CONTINUATION_LIQUIDITY_SWEEP | 430114 | 428434 | 1680 | 0 | 0 | 0 | low-sample |
| EVAL::DIVERGENCE_CONTINUATION | 430114 | 430114 | 0 | 0 | 0 | 0 | non-generating |
| EVAL::FAILED_AUCTION_RECLAIM | 430114 | 385172 | 44942 | 0 | 0 | 0 | low-sample |
| EVAL::FUNDING_EXTREME | 430114 | 430114 | 0 | 0 | 0 | 0 | non-generating |
| EVAL::LIQUIDATION_REVERSAL | 430114 | 430114 | 0 | 0 | 0 | 0 | non-generating |
| EVAL::OPENING_RANGE_BREAKOUT | 430114 | 430114 | 0 | 0 | 0 | 0 | non-generating |
| EVAL::POST_DISPLACEMENT_CONTINUATION | 430114 | 430114 | 0 | 0 | 0 | 0 | non-generating |
| EVAL::QUIET_COMPRESSION_BREAK | 430114 | 429757 | 357 | 0 | 0 | 0 | low-sample |
| EVAL::SR_FLIP_RETEST | 430114 | 420483 | 9631 | 0 | 0 | 0 | low-sample |
| EVAL::STANDARD | 430114 | 418919 | 11195 | 0 | 0 | 0 | low-sample |
| EVAL::TREND_PULLBACK | 430114 | 430025 | 89 | 0 | 0 | 0 | low-sample |
| EVAL::VOLUME_SURGE_BREAKOUT | 430114 | 430114 | 0 | 0 | 0 | 0 | non-generating |
| EVAL::WHALE_MOMENTUM | 430114 | 430114 | 0 | 0 | 0 | 0 | non-generating |
| FAILED_AUCTION_RECLAIM | 0 | 0 | 44942 | 44942 | 44942 | 0 | low-sample |
| LIQUIDITY_SWEEP_REVERSAL | 0 | 0 | 11195 | 11195 | 9863 | 4 | low-sample |
| QUIET_COMPRESSION_BREAK | 0 | 0 | 357 | 357 | 357 | 0 | low-sample |
| SR_FLIP_RETEST | 0 | 0 | 9631 | 9631 | 8582 | 32 | low-sample |
| TREND_PULLBACK_EMA | 0 | 0 | 89 | 89 | 19 | 5 | low-sample |

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
| SR_FLIP_RETEST | 0 | 9631 | 32 | 8582 | 0.0 | 0.0 | None | None | 1049 | 0 | 0 |
| TREND_PULLBACK_EMA | 0 | 89 | 5 | 19 | 0.0 | 0.0 | None | None | 70 | 0 | 0 |

## Window-over-window comparison
- Path emissions Δ: `54`
- Gating Δ: `65367`
- No-generation Δ: `5953702`
- Fast failures Δ: `0`
- Quality changes: `{"SR_FLIP_RETEST": {"avg_pnl_delta": 0.4263, "current_avg_pnl": null, "current_win_rate": null, "previous_avg_pnl": -0.4263, "previous_win_rate": 0.0, "win_rate_delta": 0.0}, "TREND_PULLBACK_EMA": {"avg_pnl_delta": 0.297, "current_avg_pnl": null, "current_win_rate": null, "previous_avg_pnl": -0.297, "previous_win_rate": 0.0, "win_rate_delta": 0.0}}`
- Post-correction setup deltas: `{"SR_FLIP_RETEST": {"emitted_delta": 32, "geometry_changed_delta": 0, "geometry_preserved_delta": 1049, "geometry_rejected_delta": 0, "median_first_breach_delta_sec": -181.05, "median_terminal_delta_sec": -184.49, "sl_rate_delta": -100.0, "win_rate_delta": 0.0}, "TREND_PULLBACK_EMA": {"emitted_delta": 5, "geometry_changed_delta": 0, "geometry_preserved_delta": 70, "geometry_rejected_delta": 0, "median_first_breach_delta_sec": -184.08, "median_terminal_delta_sec": -185.83, "sl_rate_delta": -100.0, "win_rate_delta": 0.0}}`

## Recommended operator focus
- Most suspicious degradation: **EVAL::LIQUIDATION_REVERSAL**
- Most promising healthy path: **none**
- Most likely bottleneck: **FAILED_AUCTION_RECLAIM**
- Suggested next investigation target: **EVAL::LIQUIDATION_REVERSAL**
