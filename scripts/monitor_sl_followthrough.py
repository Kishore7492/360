import json, sys, datetime
from collections import defaultdict

SL_LABELS = {"SL", "SL_HIT", "STOP_LOSS", "LOSS"}
LOOKAHEAD_SEC = 24 * 3600          # 24-hour cross-signal lookahead window
MIN_LOOKAHEAD_AGE_SEC = 4 * 3600   # skip classification if SL hit < 4h ago
MAX_RECENT_SLS = 20                 # show up to 20 most recent SL hits

def _lbl(r):
    return (r.get("outcome_label") or r.get("outcome") or r.get("status") or "").upper()

def _setup(r):
    return r.get("setup_class") or r.get("channel") or r.get("setup_type") or r.get("signal_type") or "?"

def _approx_sl_price(entry, pnl_pct, direction):
    """Reconstruct approximate SL exit price from entry and realized PnL%."""
    if not entry or entry <= 0:
        return None
    d = (direction or "").upper()
    if d == "LONG":
        return entry * (1.0 + pnl_pct / 100.0)
    elif d == "SHORT":
        return entry * (1.0 - pnl_pct / 100.0)
    return None

def _classify(record, all_chrono, now_ts):
    """
    Classify a SL_HIT record using stored MFE/hold data + cross-signal lookahead.
    Returns (classification, primary_evidence_list).
    Evidence is ordered: cross-signal findings first, then MFE/hold context.
    """
    symbol    = record.get("symbol", "?")
    direction = (record.get("direction") or "?").upper()
    entry     = record.get("entry") or 0.0
    pnl_pct   = record.get("pnl_pct") or 0.0
    mfe       = record.get("max_favorable_excursion_pct") or 0.0
    hold_sec  = record.get("hold_duration_sec") or 0.0
    sl_ts     = record.get("timestamp") or 0

    sl_depth = abs(pnl_pct)
    mfe_ratio = mfe / sl_depth if sl_depth > 0 else 0.0

    cross_signal_notes = []
    context_notes = []

    # --- insufficient-data fast path: SL too recent for reliable lookahead ---
    age_sec = now_ts - sl_ts
    if sl_ts and age_sec < MIN_LOOKAHEAD_AGE_SEC:
        hrs = age_sec / 3600
        return "insufficient data", [f"SL hit only {hrs:.1f}h ago — 24h lookahead window not complete"]

    # --- MFE context note ---
    if mfe >= 0.10:
        context_notes.append(f"MFE={mfe:+.2f}% (price moved in thesis direction before stop)")
    else:
        context_notes.append(f"MFE={mfe:+.2f}% (minimal favorable movement before stop)")

    # --- Hold duration context ---
    if hold_sec > 0:
        hold_str = f"{hold_sec/60:.0f}min" if hold_sec < 3600 else f"{hold_sec/3600:.1f}h"
        if hold_sec < 900:
            context_notes.append(f"quick-stop ({hold_str}) — price moved against thesis immediately")
        else:
            context_notes.append(f"held {hold_str}")

    # --- Cross-signal lookahead on same symbol ---
    lookahead_end = sl_ts + LOOKAHEAD_SEC
    later = [
        r for r in all_chrono
        if r.get("symbol") == symbol
        and (r.get("timestamp") or 0) > sl_ts
        and (r.get("timestamp") or 0) <= lookahead_end
    ]
    same_dir = [r for r in later if (r.get("direction") or "").upper() == direction]
    opp_dir  = [r for r in later if (r.get("direction") or "").upper() not in (direction, "?", "")]

    # Check if price reclaimed original entry (same-dir signal entry >= orig entry for LONG)
    reclaimed_entry = False
    partial_reclaim = False
    approx_sl = _approx_sl_price(entry, pnl_pct, direction)

    for r in same_dir:
        ne = r.get("entry") or 0
        if ne <= 0:
            continue
        hrs = ((r.get("timestamp") or 0) - sl_ts) / 3600
        if direction == "LONG":
            if ne >= entry:
                reclaimed_entry = True
                cross_signal_notes.append(
                    f"same-dir signal @ {ne:.4f} >= orig entry {entry:.4f} (+{hrs:.1f}h) \u2192 entry reclaimed"
                )
                break
            elif approx_sl and approx_sl < ne < entry:
                partial_reclaim = True
                cross_signal_notes.append(
                    f"same-dir signal @ {ne:.4f} between SL~{approx_sl:.4f}..entry {entry:.4f} (+{hrs:.1f}h)"
                )
                break
        elif direction == "SHORT":
            if ne <= entry:
                reclaimed_entry = True
                cross_signal_notes.append(
                    f"same-dir signal @ {ne:.4f} <= orig entry {entry:.4f} (+{hrs:.1f}h) \u2192 entry reclaimed"
                )
                break
            elif approx_sl and entry < ne < approx_sl:
                partial_reclaim = True
                cross_signal_notes.append(
                    f"same-dir signal @ {ne:.4f} between entry {entry:.4f}..SL~{approx_sl:.4f} (+{hrs:.1f}h)"
                )
                break

    if opp_dir and not reclaimed_entry and not partial_reclaim:
        hrs = ((opp_dir[0].get("timestamp") or 0) - sl_ts) / 3600
        cross_signal_notes.append(f"opposite-dir signal fired +{hrs:.1f}h after SL")

    if same_dir and not cross_signal_notes:
        # Same-dir signal fired but entry didn't clarify reclaim/partial
        hrs = ((same_dir[0].get("timestamp") or 0) - sl_ts) / 3600
        ne = same_dir[0].get("entry") or 0
        cross_signal_notes.append(f"same-dir signal @ {ne:.4f} +{hrs:.1f}h after SL (entry ratio unclear)")

    # --- Classification ---
    if reclaimed_entry:
        classification = "possible stop-too-tight / continuation"
    elif partial_reclaim:
        classification = "partial reclaim"
    elif same_dir and mfe_ratio >= 0.3:
        classification = "possible stop-too-tight / continuation"
        if not cross_signal_notes:
            hrs = ((same_dir[0].get("timestamp") or 0) - sl_ts) / 3600
            cross_signal_notes.append(f"same-dir signal +{hrs:.1f}h + MFE ratio {mfe_ratio:.0%} of stop depth")
    elif not later:
        # No subsequent signals on this symbol within lookahead
        if mfe_ratio >= 0.4:
            classification = "possible stop-too-tight / continuation"
            cross_signal_notes.append(f"MFE {mfe_ratio:.0%} of stop depth \u2014 thesis had momentum; no follow-up signal")
        elif mfe_ratio < 0.05 and hold_sec > 0 and hold_sec < 900:
            classification = "clean failure"
            cross_signal_notes.append("low MFE + quick stop; no same-symbol signals to cross-reference")
        else:
            classification = "insufficient data"
            cross_signal_notes.append("no subsequent signals on this symbol within 24h lookahead window")
    elif opp_dir and not same_dir:
        classification = "clean failure"
    elif same_dir and not reclaimed_entry and not partial_reclaim:
        classification = "partial reclaim"
    else:
        classification = "clean failure" if mfe_ratio < 0.1 else "insufficient data"

    # Build final evidence list: cross-signal notes first, then context
    evidence = cross_signal_notes + context_notes
    return classification, evidence


try:
    with open("/app/data/signal_performance.json") as f:
        data = json.load(f)

    if not data:
        print("No signal history yet \u2014 cannot compute SL follow-through analysis")
        sys.exit(0)

    # Sort chronologically (ascending) for cross-signal lookahead lookups
    all_chrono = sorted(data, key=lambda x: x.get("timestamp", 0))
    now_ts = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

    # Find SL_HIT records most-recent-first
    sl_records = [r for r in reversed(all_chrono) if _lbl(r) in SL_LABELS]

    if not sl_records:
        print("No SL_HIT records found in signal history")
        sys.exit(0)

    recent_sls = sl_records[:MAX_RECENT_SLS]
    print(f"Analyzing {len(recent_sls)} most recent SL_HIT signals  (of {len(sl_records)} total SLs | {len(data)} total signals)")
    print("")
    print(f"{'#':<3} {'Symbol':<14} {'Dir':<6} {'Setup':<30} {'Entry':>10} {'SL~(est)':>10} {'PnL%':>7} {'MFE%':>7} {'Hold':>7}  Classification")
    print("-" * 128)

    counts = defaultdict(int)

    for i, r in enumerate(recent_sls, 1):
        symbol    = r.get("symbol", "?")
        direction = (r.get("direction") or "?")
        setup     = _setup(r)
        entry     = r.get("entry") or 0.0
        pnl_pct   = r.get("pnl_pct") or 0.0
        mfe       = r.get("max_favorable_excursion_pct") or 0.0
        hold_sec  = r.get("hold_duration_sec") or 0.0
        ts        = r.get("timestamp") or 0

        ts_str    = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M") if ts else "?"
        sl_approx = _approx_sl_price(entry, pnl_pct, direction)
        sl_str    = f"{sl_approx:.4f}" if sl_approx else "n/a"
        hold_str  = (f"{hold_sec/60:.0f}m" if hold_sec < 3600 else f"{hold_sec/3600:.1f}h") if hold_sec else "n/a"

        classification, evidence = _classify(r, all_chrono, now_ts)
        counts[classification] += 1

        print(f"{i:<3} {symbol:<14} {direction:<6} {setup:<30} {entry:>10.4f} {sl_str:>10} {pnl_pct:>+7.2f}% {mfe:>+7.2f}% {hold_str:>7}  {classification}")
        for note in evidence[:2]:
            print(f"    [{ts_str}]  {note}")
        print("")

    # --- Summary block ---
    total_sl = len(recent_sls)
    print("--- SL Follow-Through Summary ---")
    for label in ["possible stop-too-tight / continuation", "partial reclaim", "clean failure", "insufficient data"]:
        n = counts[label]
        bar = "#" * n
        pct = n / total_sl * 100 if total_sl else 0
        print(f"  {label:<40}: {n:>3}/{total_sl}  ({pct:4.0f}%)  {bar}")

    valid_mfe  = [r.get("max_favorable_excursion_pct") or 0.0 for r in recent_sls]
    valid_pnl  = [r.get("pnl_pct") or 0.0 for r in recent_sls]
    valid_hold = [r.get("hold_duration_sec") or 0.0 for r in recent_sls]
    avg_mfe    = sum(valid_mfe) / len(valid_mfe) if valid_mfe else 0.0
    avg_pnl    = sum(valid_pnl) / len(valid_pnl) if valid_pnl else 0.0
    avg_hold   = sum(valid_hold) / len(valid_hold) if valid_hold else 0.0

    print("")
    print(f"  Avg SL exit PnL      : {avg_pnl:+.2f}%")
    print(f"  Avg MFE before stop  : {avg_mfe:+.2f}%")
    print(f"  Avg hold duration    : {avg_hold/60:.0f}min")
    print("")
    print("Heuristic inference \u2014 not direct post-stop price reconstruction. Based on:")
    print("  (1) stored MFE/hold_duration data from signal_performance.json, and")
    print("  (2) later same-symbol same-direction signals within a 24h window (a fresh signal")
    print("      on the same pair is not proof the original thesis continued, but is a useful proxy).")
    print("  SL~(est): approximate \u2014 reconstructed from entry + realized pnl_pct + direction;")
    print("  not exact stored SL telemetry.")
    print("")
    print("  'possible stop-too-tight / continuation' \u2014 later same-dir signal entry reclaimed orig")
    print("      entry level, or MFE>=40% of stop depth (heuristic signal of continuation bias)")
    print("  'partial reclaim'                        \u2014 same-dir signal fired between SL and orig entry")
    print("  'clean failure'                          \u2014 low MFE + quick stop, or opposite-dir signal followed")
    print("  'insufficient data'                      \u2014 SL <4h ago or no cross-reference and ambiguous MFE")

except FileNotFoundError:
    print("No signal history yet \u2014 /app/data/signal_performance.json not found")
except json.JSONDecodeError:
    print("Signal history file could not be parsed")
except Exception as e:
    import traceback
    print(f"Error in SL follow-through analysis: {e}")
    traceback.print_exc()
