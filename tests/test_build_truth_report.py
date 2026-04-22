import json
import subprocess
import sys
from pathlib import Path


def test_build_truth_report_writes_signals_last100_and_dispatch_log(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_truth_report.py"
    runtime_health = tmp_path / "runtime_health.json"
    heartbeat = tmp_path / "heartbeat.txt"
    performance = tmp_path / "signal_performance.json"
    dispatch_raw = tmp_path / "dispatch_log.json"
    current_log = tmp_path / "engine_current.log"
    previous_log = tmp_path / "engine_previous.log"
    truth_md = tmp_path / "truth_report.md"
    snapshot_json = tmp_path / "truth_snapshot.json"
    comparison_json = tmp_path / "window_comparison.json"
    signals_last100_json = tmp_path / "signals_last100.json"
    dispatch_out_json = tmp_path / "dispatch_log_out.json"

    runtime_health.write_text('{"running": true}', encoding="utf-8")
    heartbeat.write_text("ok", encoding="utf-8")
    current_log.write_text("", encoding="utf-8")
    previous_log.write_text("", encoding="utf-8")
    performance.write_text(
        json.dumps([{"timestamp": i, "signal_id": f"SIG-{i}"} for i in range(104, -1, -1)]),
        encoding="utf-8",
    )
    dispatch_raw.write_text(
        json.dumps([{"dispatch_id": i} for i in range(70)]),
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--runtime-health-json", str(runtime_health),
            "--heartbeat-text", str(heartbeat),
            "--performance-json", str(performance),
            "--dispatch-log-json", str(dispatch_raw),
            "--current-log", str(current_log),
            "--previous-log", str(previous_log),
            "--truth-report-md", str(truth_md),
            "--truth-snapshot-json", str(snapshot_json),
            "--window-comparison-json", str(comparison_json),
            "--signals-last100-json", str(signals_last100_json),
            "--dispatch-log-out-json", str(dispatch_out_json),
        ],
        check=True,
    )

    signals_payload = json.loads(signals_last100_json.read_text(encoding="utf-8"))
    assert len(signals_payload) == 100
    assert signals_payload[0]["signal_id"] == "SIG-5"
    assert signals_payload[-1]["signal_id"] == "SIG-104"

    dispatch_payload = json.loads(dispatch_out_json.read_text(encoding="utf-8"))
    assert len(dispatch_payload) == 50
    assert dispatch_payload[0]["dispatch_id"] == 20
    assert dispatch_payload[-1]["dispatch_id"] == 69
