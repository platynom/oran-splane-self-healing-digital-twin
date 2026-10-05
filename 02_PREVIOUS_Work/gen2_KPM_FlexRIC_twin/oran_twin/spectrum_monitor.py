from __future__ import annotations

from dataclasses import dataclass

from .config import Paths, load_json
from .profiles import ServiceProfile


@dataclass(frozen=True)
class SpectrumAssessment:
    spectrum_risk_score: float
    spectrum_state: str
    spectrum_action: str
    spectrum_band: str
    spectrum_channel: str
    backup_band: str
    channel_occupancy: float
    spectral_efficiency: float
    interference_source: str
    dsa_policy: str
    dsa_confidence: float
    reasons: list[str]


class SpectrumResourceMonitor:
    """SpotLight-inspired radio/spectrum resource anomaly monitor."""

    def __init__(self) -> None:
        profile = load_json(Paths.configs / "spectrum_access_profiles.json")
        self.bands = profile["bands"]
        self.interference_sources = profile["interference_sources"]

    def assess(self, row: dict[str, object], profile: ServiceProfile) -> SpectrumAssessment:
        service = str(row["service_class"])
        band_profile = self.bands.get(service, self.bands.get("eMBB", {}))
        sinr = float(row["sinr_db"])
        bler = float(row["bler_pct"])
        prb = float(row["prb_util_pct"])
        throughput = float(row["throughput_mbps"])
        latency = float(row["latency_ms"])
        jitter = float(row["jitter_ms"])
        loss = float(row["packet_loss_pct"])
        rsrp = float(row.get("rsrp_dbm", 0.0))
        rsrq = float(row.get("rsrq_db", 0.0))
        evm = float(row.get("evm_pct", 0.0))
        interference_power = float(row.get("interference_power_dbm", -120.0))
        beam_misalignment = float(row.get("beam_misalignment_deg", 0.0))
        antenna_vswr = float(row.get("antenna_vswr", 1.1))
        rf_temperature = float(row.get("rf_temperature_c", 42.0))

        score = 0.0
        reasons: list[str] = []
        target_efficiency = float(band_profile.get("target_spectral_efficiency", 0.5))
        derived_bandwidth_mhz = max(1.0, profile.throughput_mbps_target / max(target_efficiency, 0.001))
        spectral_efficiency = round(throughput / derived_bandwidth_mhz, 4)
        channel_occupancy = round(min(1.0, max(0.0, prb / 100.0 + min(0.15, bler / 100.0))), 4)

        low_sinr = sinr < 10.5
        very_low_sinr = sinr < 7.0
        high_bler = bler > 3.2
        high_prb = prb > 78.0
        throughput_collapse = throughput < profile.throughput_mbps_target * 0.58
        latency_pressure = latency > profile.latency_ms_target * 1.2

        if low_sinr and high_bler:
            score += 0.34
            reasons.append("low_sinr_high_bler_signature")
        if very_low_sinr and (jitter > profile.jitter_ms_target * 1.15 or loss > profile.packet_loss_pct_target * 1.2):
            score += 0.26
            reasons.append("interference_like_quality_drop")
        if high_prb and throughput_collapse:
            score += 0.24
            reasons.append("spectrum_resource_saturation")
        if high_prb and low_sinr and latency_pressure:
            score += 0.22
            reasons.append("radio_access_contention")
        if sinr < 12.0 and throughput < profile.throughput_mbps_target * 0.75 and bler > 2.6:
            score += 0.18
            reasons.append("dynamic_spectrum_access_watch")
        if spectral_efficiency < target_efficiency * 0.55 and channel_occupancy > float(
            band_profile.get("max_channel_occupancy", 0.8)
        ):
            score += 0.2
            reasons.append("spectral_efficiency_collapse")
        if interference_power > -78.0 and rsrq < -15.0 and evm > 8.0:
            score += 0.34
            reasons.append("oru_external_interference_signature")
        if beam_misalignment > 18.0 and rsrp < -105.0:
            score += 0.3
            reasons.append("oru_beam_misalignment_signature")
        if antenna_vswr > 2.1 or rf_temperature > 78.0:
            score += 0.28
            reasons.append("oru_rf_chain_degradation_signature")

        score = round(min(1.0, score), 4)
        if score >= 0.62:
            state = "spectrum_anomaly"
            action = "dynamic_spectrum_reassignment"
        elif score >= 0.35:
            state = "spectrum_watch"
            action = "increase_radio_resource_monitoring"
        else:
            state = "spectrum_stable"
            action = "maintain_current_radio_policy"

        source = self._interference_source(
            low_sinr,
            high_bler,
            high_prb,
            throughput_collapse,
            interference_power,
            beam_misalignment,
            antenna_vswr,
            rf_temperature,
        )
        dsa_policy = self._dsa_policy(state, source, channel_occupancy, band_profile)
        channel = self._select_channel(band_profile, row)
        confidence = self._confidence(score, reasons, source)
        if not reasons:
            reasons.append("radio_kpis_within_expected_range")
        return SpectrumAssessment(
            spectrum_risk_score=score,
            spectrum_state=state,
            spectrum_action=action,
            spectrum_band=str(band_profile.get("preferred_band", "unknown_band")),
            spectrum_channel=channel,
            backup_band=str(band_profile.get("backup_band", "unknown_backup_band")),
            channel_occupancy=channel_occupancy,
            spectral_efficiency=spectral_efficiency,
            interference_source=source,
            dsa_policy=dsa_policy,
            dsa_confidence=confidence,
            reasons=sorted(set(reasons)),
        )

    def _interference_source(
        self,
        low_sinr: bool,
        high_bler: bool,
        high_prb: bool,
        throughput_collapse: bool,
        interference_power: float,
        beam_misalignment: float,
        antenna_vswr: float,
        rf_temperature: float,
    ) -> str:
        if antenna_vswr > 2.1 or rf_temperature > 78.0:
            return "oru_rf_chain_degradation"
        if beam_misalignment > 18.0:
            return "beam_misalignment_or_blockage"
        if interference_power > -78.0:
            return "external_or_co_channel_interference"
        if low_sinr and high_bler:
            return str(self.interference_sources["low_sinr_high_bler"])
        if high_prb and throughput_collapse:
            return str(self.interference_sources["high_prb_low_throughput"])
        if high_bler and not low_sinr:
            return str(self.interference_sources["high_bler_normal_sinr"])
        if low_sinr and high_prb:
            return str(self.interference_sources["low_sinr_high_prb"])
        return "none"

    @staticmethod
    def _dsa_policy(state: str, source: str, channel_occupancy: float, band_profile: dict[str, object]) -> str:
        if state == "spectrum_stable":
            return "hold_current_channel"
        if state == "spectrum_watch":
            return "probe_backup_channel_and_raise_sampling"
        if source in {"co_channel_or_external_interference", "coverage_edge_contention"}:
            return f"switch_to_backup_band_{band_profile.get('backup_band', 'backup')}"
        if channel_occupancy > float(band_profile.get("max_channel_occupancy", 0.8)):
            return "rebalance_users_across_channel_pool"
        return "reduce_mcs_and_monitor_interference"

    @staticmethod
    def _select_channel(band_profile: dict[str, object], row: dict[str, object]) -> str:
        pool = list(band_profile.get("channel_pool", ["unknown_channel"]))
        cell = str(row.get("cell_id", "CELL_A"))
        index = sum(ord(char) for char in cell) % max(1, len(pool))
        return str(pool[index])

    @staticmethod
    def _confidence(score: float, reasons: list[str], source: str) -> float:
        confidence = 0.58 + score * 0.34 + min(0.08, len(reasons) * 0.015)
        if source != "none":
            confidence += 0.06
        return round(min(0.98, confidence), 4)
