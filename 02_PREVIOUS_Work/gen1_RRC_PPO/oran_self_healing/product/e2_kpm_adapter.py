"""
Live Near-RT RIC adapter STUB (E2SM-KPM -> governor -> E2 control).

This is the concrete interface for the production/live path. It does NOT talk to
a real RIC yet - it defines the exact seam so a FlexRIC/OSC-RIC xApp can plug in.
Replace `receive_indications()` and `send_control()` with real E2AP/E2SM-KPM bindings
(e.g. via FlexRIC's Python xApp SDK) on your testbed.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from engine import GovernanceEngine
from persistence import load_artifacts
from lite_components import LitePolicyAgent


# ---- map an E2SM-KPM measurement record to our KPM dict ----
def kpm_indication_to_dict(ind):
    """`ind` is one decoded E2SM-KPM indication. Adjust field names to your
    measurement set. This mapping is the single integration point."""
    m = ind.get("measData", ind)
    return {
        "ue_id": ind.get("ueId", 0),
        "rsrp": m.get("RSRP", -80),
        "rsrq": m.get("RSRQ", -12),
        "sinr": m.get("SINR", 20),
        "cqi": m.get("CQI", 12),
        "neighbor_rsrp_1": m.get("neighborRSRP", -90),
        "network_load": m.get("RRU.PrbTotDl", 0.4),
        "latency_ms": m.get("DRB.RlcSduDelayDl", 20),
        "packet_loss": m.get("packetLossRate", 0.02),
        "rrc_state": m.get("rrcState", "RRC_CONNECTED"),
    }


# ---- map a governor action to an E2 control message ----
def action_to_e2_control(ue_id, decision):
    return {"ueId": ue_id, "controlAction": decision["action_name"],
            "reason": decision["reason"], "confidence": decision["confidence"]}


def receive_indications():
    """REPLACE with real E2 subscription stream. Yields decoded indications."""
    raise NotImplementedError("Bind to FlexRIC/OSC-RIC E2SM-KPM subscription here.")


def send_control(msg):
    """REPLACE with real E2AP RIC Control Request."""
    raise NotImplementedError("Bind to E2AP RIC Control here.")


def run_xapp():
    gate, guard, _ = load_artifacts("artifacts")
    engine = GovernanceEngine(gate, guard, LitePolicyAgent())
    for ind in receive_indications():             # live E2SM-KPM stream
        kpm = kpm_indication_to_dict(ind)
        decision = engine.decide(kpm)
        if decision["action_name"] != "keep_connected":
            send_control(action_to_e2_control(kpm["ue_id"], decision))


if __name__ == "__main__":
    print("E2/KPM adapter stub. Implement receive_indications()/send_control() "
          "against your FlexRIC/OSC-RIC testbed, then call run_xapp().")
