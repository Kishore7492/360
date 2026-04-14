import json, sys, datetime
from collections import defaultdict

def _lbl(r):
    return (r.get("outcome_label") or r.get("outcome") or r.get("status") or "").upper()

# Deliberately-classified outcome sets based on live-observed labels
TP_LABELS  = {"TP", "TP1", "TP2", "TP3", "TP_HIT", "TP1_HIT", "TP2_HIT", "TP3_HIT", "TAKE_PROFIT", "WIN"}
SL_LABELS  = {"SL", "SL_HIT", "STOP_LOSS", "LOSS"}
EXP_LABELS = {"EXPIRED", "EXPIRY"}
# CLOSED and INVALIDATED are tracked separately: CLOSED may be manual/external exit,
# INVALIDATED is a pre-entry invalidation — both are distinct from SL/TP
CLOSED_LABELS     = {"CLOSED"}
INVALIDATED_LABELS = {"INVALIDATED", "CANCELLED", "CANCEL"}

try:
    with open("/app/data/signal_performance.json") as f:
        data = json.load(f)
    if not data:
        print("No signal history yet")
        sys.exit(0)

    all_records = sorted(data, key=lambda x: x.get("timestamp", 0), reverse=True)
    total = len(all_records)
    window = min(50, total)

    print(f"Total signals on record: {total}  |  Showing most recent {window}")
    print("")
    print(f"{'#':<3} {'Symbol':<14} {'Dir':<6} {'Setup':<32} {'Conf':>6} {'PnL%':>7} {'Outcome':<14} {'Time'}")
    print("-" * 112)
    for i, r in enumerate(all_records[:50], 1):
        ts = r.get("timestamp", 0)
        ts_str = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M") if ts else "?"
        outcome = r.get("outcome_label") or r.get("outcome") or r.get("status") or "?"
        setup = r.get("setup_class") or r.get("channel") or r.get("setup_type") or r.get("signal_type") or "?"
        pnl = r.get("pnl_pct") or 0.0
        print(f"{i:<3} {r.get('symbol','?'):<14} {r.get('direction','?'):<6} {setup:<32} {r.get('confidence',0):>6.1f} {pnl:>+7.2f}% {outcome:<14} {ts_str}")

    # --- By-path/setup breakdown (full history) ---
    print("")
    print("--- By-Path / Setup Summary (full history) ---")
    by_setup = defaultdict(list)
    for r in all_records:
        key = r.get("setup_class") or r.get("channel") or r.get("setup_type") or r.get("signal_type") or "?"
        by_setup[key].append(r)

    print(f"{'Setup/Path':<34} {'N':>4} {'TP':>4} {'SL':>4} {'Exp':>4} {'Closed':>6} {'Inv':>4} {'Other':>6} {'AvgConf':>8} {'AvgPnL%':>8}  Latest")
    print("-" * 130)
    for setup_key in sorted(by_setup.keys()):
        recs = by_setup[setup_key]
        count = len(recs)
        tp_n   = sum(1 for r in recs if _lbl(r) in TP_LABELS)
        sl_n   = sum(1 for r in recs if _lbl(r) in SL_LABELS)
        exp_n  = sum(1 for r in recs if _lbl(r) in EXP_LABELS)
        cls_n  = sum(1 for r in recs if _lbl(r) in CLOSED_LABELS)
        inv_n  = sum(1 for r in recs if _lbl(r) in INVALIDATED_LABELS)
        other_n = count - tp_n - sl_n - exp_n - cls_n - inv_n
        confs = [r.get("confidence", 0) for r in recs if r.get("confidence")]
        pnls  = [r.get("pnl_pct", 0.0) for r in recs if r.get("pnl_pct") is not None]
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        avg_pnl  = sum(pnls)  / len(pnls)  if pnls  else 0.0
        latest = max(recs, key=lambda x: x.get("timestamp", 0))
        last_out = latest.get("outcome_label") or latest.get("outcome") or latest.get("status") or "?"
        last_ts  = latest.get("timestamp", 0)
        last_ts_str = datetime.datetime.fromtimestamp(last_ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M") if last_ts else "?"
        print(f"{setup_key:<34} {count:>4} {tp_n:>4} {sl_n:>4} {exp_n:>4} {cls_n:>6} {inv_n:>4} {other_n:>6} {avg_conf:>8.1f} {avg_pnl:>+8.2f}%  {last_out}@{last_ts_str}")

except FileNotFoundError:
    print("No signal history yet")
except json.JSONDecodeError:
    print("Signal history file could not be parsed")
except Exception as e:
    print(f"Error reading signal history: {e}")
