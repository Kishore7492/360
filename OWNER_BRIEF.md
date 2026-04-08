| `_evaluate_volume_surge_breakout` — VOLUME_SURGE_BREAKOUT | ✅ Active |
| `_evaluate_breakdown_short` — BREAKDOWN_SHORT | ✅ Active |

### PR8 — New Signal Paths + Dynamic Discovery + Method-Specific SL/TP ✅ MERGED (PR #54, 2026-04-08)

| Current State Snapshot |
| PR8 | ✅ Merged — 2 new signal paths, dynamic promotion, structural SL/TP, expiry notifications |
| Deep research audit | ✅ Complete — findings incorporated into PR8 and PR9 spec |
| PR9 spec | ⏳ Ready to spec — raise after PR8 settles on VPS |
| Testing phase | ⏳ Not started — begins after PR9 merges |

**2026-04-08 — PR8 merged (PR #54):**
- VOLUME_SURGE_BREAKOUT and BREAKDOWN_SHORT signal paths now live
- Dynamic pair promotion live — surging pairs outside top-75 enter scan within one cycle
- Structure-based SL/TP now active on LIQUIDITY_SWEEP_REVERSAL and TREND_PULLBACK paths
- Signal expiry Telegram notifications live — no more silent disappearances
- New config vars live: SURGE_VOLUME_MULTIPLIER=3.0, SURGE_PROMOTION_VOLUME_MULTIPLIER=5.0, SURGE_PROMOTION_MAX_PAIRS=5
- Next: monitor live engine for surge signal firing on volatile days. Raise PR9 spec.