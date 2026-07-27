# Demo Script

## Opening Claim

This is a RIC-ready O-RAN digital twin prototype for safe AI self-healing. It compares a baseline self-healing loop against a guarded loop that checks AML, drift, xApp conflict, SLA, timing, spectrum, ZSM policy, DTN readiness, and automation safety before allowing action.

## Live Demo Steps

1. Start the GUI:

```powershell
python live_backend.py --port 8080
```

2. Open:

```text
http://127.0.0.1:8080/
```

3. Show the virtual device population panel.

Explain that lakhs of devices are represented as service-level aggregates, while representative UE samples are shown for readability.

4. Select a fault:

```text
cell_congestion
```

5. Show:

- risk score
- RCA
- healing action
- automation safety score
- baseline loop
- guarded loop
- safety improvement

6. Select:

```text
spectrum_interference
```

Show the dynamic spectrum access decision.

7. Select:

```text
telemetry_poisoning
```

Show the AML guard and blocked automation behavior.

## Batch Evidence

Run:

```powershell
python run_demo.py --run-name local_hardening_full --duration 240 --seed 42
```

Use:

```text
outputs/runs/local_hardening_full/evaluation_report.md
outputs/runs/local_hardening_full/incident_report.md
```

Main line:

```text
The baseline would execute 875 recovery actions. The guarded layer allows 513 and prevents 362 unsafe baseline actions.
```
