# Runtime Truth Report

## Executive summary
- Overall health/freshness: **healthy**
- Top anomalies/concerns: none
- Top promising signals/paths: none
- Recommended next investigation target: **none**

## Runtime health
- Engine running: `True` (status=running, health=healthy)
- Heartbeat age: `55` sec (warning=False)
- Latest performance record age: `5823` sec

## Path funnel truth
| Path/Setup | Attempts | No-signal | Generated | Scanner prep | Gated | Emitted | Classification |
|---|---:|---:|---:|---:|---:|---:|---|

## Evaluator no-signal reasons

## Dependency readiness

## Lifecycle truth summary
- Median create→dispatch: `4.475738048553467` sec
- Median create→first breach: `184.48660111427307` sec
- Median create→terminal: `211.3614649772644` sec
- Median first breach→terminal: `6.680773973464966` sec
- Fast-failure buckets: `{"under_120s": {"count": 0, "pct": 0.0}, "under_180s": {"count": 0, "pct": 0.0}, "under_30s": {"count": 0, "pct": 0.0}, "under_60s": {"count": 0, "pct": 0.0}}`
- ~3 minute terminal-close behavior: `{"count": 24, "pct": 55.8}`

## Quality-by-path/setup summary
| Path/Setup | Emitted | Closed | Win rate | SL rate | TP rate | Avg PnL% | Median first breach (s) | Median terminal (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CONTINUATION_LIQUIDITY_SWEEP | 1 | 1 | 0.0 | 100.0 | 0.0 | -1.1325 | 185.00471901893616 | 186.09579491615295 |
| FAILED_AUCTION_RECLAIM | 9 | 9 | 0.0 | 0.0 | 0.0 | 1.5372 | 185.23825109004974 | 631.5399980545044 |
| LIQUIDITY_SWEEP_REVERSAL | 1 | 1 | 0.0 | 0.0 | 0.0 | 4.6377 | 185.57982683181763 | 203.14849281311035 |
| QUIET_COMPRESSION_BREAK | 1 | 1 | 0.0 | 100.0 | 0.0 | -0.917 | 180.5619330406189 | 181.33109498023987 |
| SR_FLIP_RETEST | 8 | 8 | 0.0 | 37.5 | 0.0 | 0.0387 | 183.23200798034668 | 632.899242401123 |
| TREND_PULLBACK_EMA | 23 | 23 | 0.0 | 78.3 | 0.0 | -0.0947 | 184.48791480064392 | 193.67181396484375 |

## Post-correction focus (target setups)
| Setup | Attempts | Generated | Emitted | Gated | Win rate | SL rate | Median first breach (s) | Median terminal (s) | Geometry preserved | Geometry changed | Geometry rejected |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SR_FLIP_RETEST | 0 | 0 | 0 | 0 | 0.0 | 37.5 | 183.23200798034668 | 632.899242401123 | 0 | 0 | 0 |
| TREND_PULLBACK_EMA | 0 | 0 | 0 | 0 | 0.0 | 78.3 | 184.48791480064392 | 193.67181396484375 | 0 | 0 | 0 |

## Window-over-window comparison
- Path emissions Δ: `0`
- Gating Δ: `0`
- No-generation Δ: `0`
- Fast failures Δ: `0`
- Quality changes: `{"FAILED_AUCTION_RECLAIM": {"avg_pnl_delta": 1.5372, "current_avg_pnl": 1.5372, "current_win_rate": 0.0, "previous_avg_pnl": null, "previous_win_rate": null, "win_rate_delta": 0.0}, "SR_FLIP_RETEST": {"avg_pnl_delta": 0.0387, "current_avg_pnl": 0.0387, "current_win_rate": 0.0, "previous_avg_pnl": null, "previous_win_rate": null, "win_rate_delta": 0.0}, "TREND_PULLBACK_EMA": {"avg_pnl_delta": -0.0947, "current_avg_pnl": -0.0947, "current_win_rate": 0.0, "previous_avg_pnl": null, "previous_win_rate": null, "win_rate_delta": 0.0}}`
- Post-correction setup deltas: `{"SR_FLIP_RETEST": {"emitted_delta": 0, "geometry_changed_delta": 0, "geometry_preserved_delta": 0, "geometry_rejected_delta": 0, "median_first_breach_delta_sec": 183.23, "median_terminal_delta_sec": 632.9, "sl_rate_delta": 37.5, "win_rate_delta": 0.0}, "TREND_PULLBACK_EMA": {"emitted_delta": 0, "geometry_changed_delta": 0, "geometry_preserved_delta": 0, "geometry_rejected_delta": 0, "median_first_breach_delta_sec": 184.49, "median_terminal_delta_sec": 193.67, "sl_rate_delta": 78.3, "win_rate_delta": 0.0}}`

## Recommended operator focus
- Most suspicious degradation: **none**
- Most promising healthy path: **none**
- Most likely bottleneck: **none**
- Suggested next investigation target: **none**
