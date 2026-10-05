# Service Profile Numeric Assumptions

The service-class parameters in `service_profiles.json` are modeled as project-level slice targets, not exact operator SLA commitments.

Grounding sources:

- 3GPP TS 23.501 defines 5QI/QoS characteristics such as packet delay budget, packet error rate, priority, averaging window, and example services.
- ITU IMT-2020 requirements define high-level 5G targets, including low latency for URLLC, high reliability, high connection density for mMTC, high mobility support, and high throughput for eMBB.
- The project extends these classes with FWA and V2X as service categories for Digital Twin simulation.
- Open-Meteo provides live weather enrichment for Bengaluru. Weather is not a telecom KPI, but rain/wind are useful external context for RF and field-maintenance risk.

Practical modeling rule:

- Use the user's qualitative profile format as the semantic model.
- Convert qualitative targets into numeric thresholds for simulation and AI decisions.
- Keep high-criticality profiles such as URLLC and V2X stricter than eMBB/FWA/mMTC.
- Treat values as configurable assumptions, not immutable telecom standards.
- Use actual operator/OAI counters later when available; until then, generated RAN KPIs are profile-driven synthetic telemetry.

References:

- 3GPP TS 23.501 / ETSI TS 123 501, 5G System Architecture and 5QI QoS characteristics: https://www.etsi.org/deliver/etsi_ts/123500_123599/123501/
- ITU-R Report M.2410, minimum requirements related to technical performance for IMT-2020 radio interfaces: https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-M.2410-2017-TOC-HTM-E.htm
- Open-Meteo Forecast API documentation: https://open-meteo.com/en/docs
