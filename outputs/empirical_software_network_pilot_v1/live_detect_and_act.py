"""S9/S11 live detector: streams pcap from stdin, runs the FROZEN detector, fires one command.

The detection engine is imported unchanged. Only the I/O is new. The detector never sees a
filename, a scenario, or any future packet: frames are consumed one at a time as they arrive.
"""
from __future__ import annotations
import argparse, json, os, struct, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1] / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(APP))
from streaming_discriminator_v1 import packet_from_frame, tick                  # noqa: E402
from streaming_discriminator_v3_nonoverlap import NonoverlapV3State, observe_nonoverlap_v3  # noqa: E402

TRIGGER = "NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED"


def read_exact(stream, n: int) -> bytes | None:
    buf = b""
    while len(buf) < n:
        chunk = stream.read(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream-id", required=True, help="stable identifier; NOT a filename")
    ap.add_argument("--action-command", default="", help="shell command to run once on trigger; empty = no-action arm")
    ap.add_argument("--arm", required=True, choices=["action", "no_action"])
    ap.add_argument("--decision-log", required=True)
    ap.add_argument("--max-seconds", type=float, default=120.0)
    args = ap.parse_args()

    log = open(args.decision_log, "w", encoding="utf-8")

    def record(event: str, **kw):
        row = {"event": event, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "monotonic_s": round(time.monotonic(), 6), "arm": args.arm, **kw}
        log.write(json.dumps(row) + "\n"); log.flush()

    stdin = sys.stdin.buffer
    gh = read_exact(stdin, 24)
    if gh is None:
        record("stream_error", detail="no pcap global header"); return
    magic = struct.unpack("<I", gh[:4])[0]
    endian = "<" if magic in (0xA1B2C3D4, 0xA1B23C4D) else ">"
    divisor = 1e9 if magic in (0xA1B23C4D, 0x4D3CB2A1) else 1e6
    record("stream_started", stream_id=args.stream_id, pcap_magic=hex(magic), ts_divisor=divisor,
           action_command=(args.action_command or None))

    state = NonoverlapV3State()
    fired = False
    started = time.monotonic()
    frames = 0
    while time.monotonic() - started < args.max_seconds:
        hdr = read_exact(stdin, 16)
        if hdr is None:
            record("stream_ended", frames=frames); break
        ts_sec, ts_sub, incl, _orig = struct.unpack(endian + "IIII", hdr)
        data = read_exact(stdin, incl)
        if data is None:
            record("stream_truncated", frames=frames); break
        frames += 1
        ts = ts_sec + ts_sub / divisor
        out = observe_nonoverlap_v3(state, packet_from_frame(args.stream_id, ts, data))
        for ev in out["events"]:
            record("independent_event", type=ev["type"], packet_ts=ts)
        if out["classification"] == TRIGGER and not fired:
            fired = True
            record("detection_trigger", classification=TRIGGER, reason=out["reason"],
                   packet_ts=ts, frames_consumed=frames)
            if args.arm == "no_action" or not args.action_command:
                record("action_withheld", detail="no_action arm: matched control, nothing executed")
            else:
                record("action_intent", command=args.action_command)
                t0 = time.monotonic()
                proc = subprocess.run(args.action_command, shell=True, capture_output=True, text=True)
                record("action_execution_result", returncode=proc.returncode,
                       elapsed_s=round(time.monotonic() - t0, 6),
                       stdout_bytes=len(proc.stdout), stderr_text=proc.stderr.strip()[:400])
    record("detector_finished", frames=frames, triggered=fired)
    log.close()


if __name__ == "__main__":
    main()
