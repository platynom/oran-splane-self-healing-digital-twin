# llm_governor.py
# NOVELTY COMPONENT (4/4): LLM safety governor above the PPO healing agent.
# For every anomaly the LSTM gate raises it answers, BEFORE any RRC action:
#   1. CAUSE  -> benign / genuine_fault / adversarial(spoofed) ?
#   2. ACTION -> is the RL agent's action safe to execute?
#   3. WHY    -> an auditable natural-language justification + confidence.
# It fuses three evidence sources: anomaly score (LSTM), AML-guard physical
# consistency report, and the digital-twin counterfactual forecast.
# backend="offline" (default) = transparent deterministic reasoning (no keys).
# backend="claude"           = same context sent to the Claude API (drop-in).
import os
import json

ACTION_NAMES = ["trigger_handover", "delay_handover", "modify_threshold",
                "adjust_report_interval", "idle_transition", "keep_connected"]
SAFE_DEFAULT = 5
HARMFUL_ACTIONS = {0, 1, 4}

CLAUDE_SYSTEM = (
    "You are a safety governor for an O-RAN RRC self-healing loop. You receive a "
    "KPM snapshot, an anomaly score, an adversarial-consistency report, and a "
    "digital-twin forecast for a proposed RRC action. Decide the true CAUSE of the "
    "anomaly and whether the proposed action is safe. A genuine radio fault moves "
    "coupled KPMs together (RSRP, SINR, CQI, packet-loss). An adversarial/spoofed "
    "report manipulates one KPM while leaving the physically-coupled ones "
    "inconsistent. Never let a spoofed report trigger a handover or idle "
    'transition. Respond ONLY as JSON: {"cause":"benign|genuine_fault|adversarial",'
    '"action":"<one of the 6 action names>","verdict":"commit|override|veto",'
    '"confidence":0-1,"reason":"<one sentence>"}'
)


class GovernorDecision(dict):
    __getattr__ = dict.get


def _snapshot_is_healthy(s):
    """A physically healthy instantaneous snapshot -> the alarm is a false alarm
    from the windowed gate (an anomaly nearby, not here)."""
    return (s["rsrp"] > -100 and s["sinr"] > 8 and s["packet_loss"] < 0.10
            and s["network_load"] < 0.85 and s["latency_ms"] < 40)


class LLMGovernor:
    def __init__(self, backend="offline", model="claude-sonnet-5", aml_high=0.6):
        self.backend = backend
        self.model = model
        self.aml_high = aml_high
        self._client = None
        if backend == "claude":
            self._init_claude()

    def _init_claude(self):
        try:
            import anthropic
            key = os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                print("[governor] no ANTHROPIC_API_KEY -> offline.")
                self.backend = "offline"; return
            self._client = anthropic.Anthropic(api_key=key)
        except Exception as e:
            print(f"[governor] anthropic unavailable ({e}) -> offline.")
            self.backend = "offline"

    def decide(self, context):
        if self.backend == "claude" and self._client is not None:
            try:
                return self._decide_claude(context)
            except Exception as e:
                print(f"[governor] claude failed ({e}) -> offline.")
        return self._decide_offline(context)

    def _decide_offline(self, ctx):
        snap = ctx["snapshot"]
        rl_action = int(ctx["rl_action"])
        aml_flag = bool(ctx["aml_flag"])
        aml_score = float(ctx["aml_score"])
        anomaly_flag = bool(ctx["anomaly_flag"])
        bd = ctx.get("aml_breakdown", {})
        fc = ctx.get("twin_forecast", {})

        # A) no anomaly -> hold
        if not anomaly_flag:
            return GovernorDecision(cause="benign", action=SAFE_DEFAULT,
                verdict="commit", confidence=0.9,
                reason="No anomaly on the gate; maintaining the connection.")

        # B) anomaly + physically inconsistent -> ADVERSARIAL -> veto
        if aml_flag or aml_score >= self.aml_high:
            worst = bd.get("worst_violation", "cross-feature")
            return GovernorDecision(cause="adversarial", action=SAFE_DEFAULT,
                verdict="veto",
                confidence=round(min(0.55 + aml_score / 2, 0.99), 2),
                reason=(f"Anomaly violates physical invariant '{worst}': one KPM "
                        f"was manipulated while its coupled KPMs stayed inconsistent. "
                        f"This matches a spoofed KPM report, not a real fault. "
                        f"Vetoing '{ACTION_NAMES[rl_action]}' and holding the "
                        f"connection to neutralise the attack."))

        # C) anomaly but instantaneous KPMs are healthy -> false alarm -> benign
        if _snapshot_is_healthy(snap):
            return GovernorDecision(cause="benign", action=SAFE_DEFAULT,
                verdict="override", confidence=0.75,
                reason=("Gate raised an alarm but this snapshot is physically "
                        "healthy (RSRP/SINR/packet-loss nominal); treating as a "
                        "false alarm and holding the connection."))

        # D) anomaly + consistent + degraded -> GENUINE FAULT -> twin-shielded heal
        twin_action = fc.get("approved_action", rl_action)
        if fc.get("decision") == "override_to_safe_default":
            return GovernorDecision(cause="genuine_fault", action=SAFE_DEFAULT,
                verdict="override", confidence=0.7,
                reason=(f"Genuine fault, but the twin rates "
                        f"'{ACTION_NAMES[rl_action]}' (r={fc.get('reward_proposed')}) "
                        f"no better than holding (r={fc.get('reward_safe_default')}); "
                        f"overriding to avoid an unnecessary reconfiguration."))
        return GovernorDecision(cause="genuine_fault", action=int(twin_action),
            verdict="commit", confidence=0.8,
            reason=(f"Genuine fault confirmed (KPMs consistent and degraded); twin "
                    f"supports '{ACTION_NAMES[int(twin_action)]}' "
                    f"(r={fc.get('reward_proposed')} vs hold "
                    f"r={fc.get('reward_safe_default')}); committing the heal."))

    def _decide_claude(self, ctx):
        payload = {
            "snapshot": {k: round(float(v), 3) for k, v in ctx["snapshot"].items()},
            "anomaly_score": round(float(ctx["anomaly_score"]), 3),
            "aml_report": ctx.get("aml_breakdown", {}),
            "aml_score": round(float(ctx["aml_score"]), 3),
            "rl_proposed_action": ACTION_NAMES[int(ctx["rl_action"])],
            "twin_forecast": ctx.get("twin_forecast", {}),
        }
        msg = self._client.messages.create(model=self.model, max_tokens=300,
            system=CLAUDE_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(payload)}])
        txt = msg.content[0].text.strip()
        txt = txt[txt.find("{"): txt.rfind("}") + 1]
        out = json.loads(txt)
        act = out.get("action", "keep_connected")
        act_idx = ACTION_NAMES.index(act) if act in ACTION_NAMES else SAFE_DEFAULT
        return GovernorDecision(cause=out.get("cause", "benign"), action=act_idx,
            verdict=out.get("verdict", "commit"),
            confidence=float(out.get("confidence", 0.5)),
            reason=out.get("reason", ""))
