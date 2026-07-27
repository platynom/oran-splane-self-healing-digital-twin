let serviceProfiles = {};
let cells = [];
let mecNodes = [];

const state = {
  selectedCell: "CELL_A",
  t: 0,
  current: null,
  apiOnline: false,
  kpmDataset: null,
  liveTelemetry: null,
};

const map = L.map("map", { zoomControl: true }).setView([12.9716, 77.5946], 11);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const cellLayer = L.layerGroup().addTo(map);
const mecLayer = L.layerGroup().addTo(map);

const els = {
  serviceClass: document.getElementById("serviceClass"),
  targetCell: document.getElementById("targetCell"),
  faultType: document.getElementById("faultType"),
  severity: document.getElementById("severity"),
  networkLoad: document.getElementById("networkLoad"),
  mobility: document.getElementById("mobility"),
  weather: document.getElementById("weather"),
  healingMode: document.getElementById("healingMode"),
  severityValue: document.getElementById("severityValue"),
  networkLoadValue: document.getElementById("networkLoadValue"),
  mobilityValue: document.getElementById("mobilityValue"),
  weatherValue: document.getElementById("weatherValue"),
  telemetryMode: document.getElementById("telemetryMode"),
  telemetrySource: document.getElementById("telemetrySource"),
  telemetryStatus: document.getElementById("telemetryStatus"),
  liveTelemetryStatus: document.getElementById("liveTelemetryStatus"),
  liveTelemetryMatrix: document.getElementById("liveTelemetryMatrix"),
  populationSummary: document.getElementById("populationSummary"),
  populationMatrix: document.getElementById("populationMatrix"),
  modelRegistry: document.getElementById("modelRegistry"),
  kpmDatasetSummary: document.getElementById("kpmDatasetSummary"),
  kpmDatasetMatrix: document.getElementById("kpmDatasetMatrix"),
  profileDetails: document.getElementById("profileDetails"),
  profileMatrix: document.getElementById("profileMatrix"),
  riskScore: document.getElementById("riskScore"),
  slaStatus: document.getElementById("slaStatus"),
  postRisk: document.getElementById("postRisk"),
  automationSafety: document.getElementById("automationSafety"),
  safetyDecision: document.getElementById("safetyDecision"),
  predictiveHorizon: document.getElementById("predictiveHorizon"),
  aiTrust: document.getElementById("aiTrust"),
  amlThreat: document.getElementById("amlThreat"),
  driftStatus: document.getElementById("driftStatus"),
  driftScore: document.getElementById("driftScore"),
  xappConflict: document.getElementById("xappConflict"),
  selectedXapp: document.getElementById("selectedXapp"),
  slaImpact: document.getElementById("slaImpact"),
  timingState: document.getElementById("timingState"),
  spectrumState: document.getElementById("spectrumState"),
  spectrumRisk: document.getElementById("spectrumRisk"),
  kpiGrid: document.getElementById("kpiGrid"),
  openRanReplayRow: document.getElementById("openRanReplayRow"),
  openRanUeChart: document.getElementById("openRanUeChart"),
  openRanUeTable: document.getElementById("openRanUeTable"),
  rootCause: document.getElementById("rootCause"),
  confidence: document.getElementById("confidence"),
  healingAction: document.getElementById("healingAction"),
  baselineAction: document.getElementById("baselineAction"),
  guardedAction: document.getElementById("guardedAction"),
  safetyImprovement: document.getElementById("safetyImprovement"),
  validation: document.getElementById("validation"),
  securityGuard: document.getElementById("securityGuard"),
  threatType: document.getElementById("threatType"),
  driftType: document.getElementById("driftType"),
  modelAction: document.getElementById("modelAction"),
  conflictStrategy: document.getElementById("conflictStrategy"),
  policyState: document.getElementById("policyState"),
  spectrumAction: document.getElementById("spectrumAction"),
  customerImpact: document.getElementById("customerImpact"),
  ueSamples: document.getElementById("ueSamples"),
  timeline: document.getElementById("timeline"),
  overallState: document.getElementById("overallState"),
  clockLabel: document.getElementById("clockLabel"),
};

async function init() {
  bindEvents();
  updateSliderLabels();
  await fetchKpmDataset();
  await fetchLiveTelemetry();
  await fetchState();
  setInterval(fetchState, 1000);
  setInterval(fetchLiveTelemetry, 3000);
}

function bindEvents() {
  ["serviceClass", "targetCell", "faultType", "healingMode"].forEach((id) => {
    els[id].addEventListener("change", applyScenario);
  });
  ["severity", "networkLoad", "mobility", "weather"].forEach((id) => {
    els[id].addEventListener("input", () => {
      updateSliderLabels();
      applyScenario();
    });
  });
  document.getElementById("applyScenario").addEventListener("click", applyScenario);
  document.getElementById("resetScenario").addEventListener("click", resetScenario);
  document.getElementById("applyTelemetry").addEventListener("click", applyTelemetry);
  els.telemetryMode.addEventListener("change", () => {
    if (els.telemetryMode.value === "open_ran_kpm_replay") {
      els.telemetrySource.value = "data/training/open_ran_kpm_training_dataset.csv";
    }
  });
}

async function fetchState() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`API ${response.status}`);
    const data = await response.json();
    state.apiOnline = true;
    applySnapshot(data);
  } catch (error) {
    state.apiOnline = false;
    els.clockLabel.textContent = "Backend offline";
    els.timeline.innerHTML = `<li>Start the live backend with <strong>python live_backend.py --port 8080</strong>.</li>`;
  }
}

async function fetchKpmDataset() {
  try {
    const response = await fetch("/api/kpm-dataset", { cache: "no-store" });
    if (!response.ok) throw new Error(`API ${response.status}`);
    state.kpmDataset = await response.json();
    renderKpmDataset(state.kpmDataset);
  } catch (error) {
    if (els.kpmDatasetSummary) {
      els.kpmDatasetSummary.textContent = `Open RAN KPM summary unavailable: ${error.message}`;
    }
  }
}

async function fetchLiveTelemetry() {
  try {
    const response = await fetch("/api/live-telemetry", { cache: "no-store" });
    if (!response.ok) throw new Error(`API ${response.status}`);
    state.liveTelemetry = await response.json();
    renderLiveTelemetry(state.liveTelemetry);
  } catch (error) {
    if (els.liveTelemetryStatus) {
      els.liveTelemetryStatus.textContent = `Live telemetry status unavailable: ${error.message}`;
    }
  }
}

function applySnapshot(data) {
  serviceProfiles = data.profiles || {};
  cells = data.cells || [];
  mecNodes = data.mecNodes || [];
  state.t = data.t || 0;
  state.current = data.current;
  state.selectedCell = data.scenario?.target_cell || state.selectedCell;

  syncControls(data.scenario || {});
  renderMecNodes();
  renderTelemetry(data.telemetry, data.sources);
  renderPopulation(data.current?.devicePopulation);
  renderModelRegistry(data.modelRegistry);
  renderProfile(data.current?.profile, data.weather);
  renderOutputs(data.current?.selected, data.current, data.weather);
  renderOpenRanUeView(data.history || []);
  renderCells(data.current?.cells || []);
}

function syncControls(scenario) {
  fillCellOptions();
  if (scenario.service && els.serviceClass.value !== scenario.service) els.serviceClass.value = scenario.service;
  if (scenario.target_cell && els.targetCell.value !== scenario.target_cell) els.targetCell.value = scenario.target_cell;
  if (scenario.fault_type && els.faultType.value !== scenario.fault_type) els.faultType.value = scenario.fault_type;
  if (scenario.healing_mode && els.healingMode.value !== scenario.healing_mode) els.healingMode.value = scenario.healing_mode;
  setSlider(els.severity, scenario.severity);
  setSlider(els.networkLoad, scenario.network_load);
  setSlider(els.mobility, scenario.mobility);
  if (scenario.weather_impact_override !== null && scenario.weather_impact_override !== undefined) {
    setSlider(els.weather, scenario.weather_impact_override);
  }
  updateSliderLabels();
}

function fillCellOptions() {
  const existing = Array.from(els.targetCell.options).map((option) => option.value).join(",");
  const incoming = cells.map((cell) => cell.id).join(",");
  if (existing === incoming) return;
  els.targetCell.innerHTML = "";
  cells.forEach((cell) => {
    const option = document.createElement("option");
    option.value = cell.id;
    option.textContent = `${cell.id} - ${cell.site}`;
    els.targetCell.appendChild(option);
  });
}

function setSlider(input, value) {
  if (value === undefined || value === null) return;
  const next = String(Math.round(Number(value) * 100));
  if (input.value !== next) input.value = next;
}

function updateSliderLabels() {
  els.severityValue.textContent = `${els.severity.value}%`;
  els.networkLoadValue.textContent = `${els.networkLoad.value}%`;
  els.mobilityValue.textContent = `${els.mobility.value}%`;
  els.weatherValue.textContent = `${els.weather.value}%`;
}

async function applyScenario() {
  updateSliderLabels();
  const payload = {
    service: els.serviceClass.value,
    target_cell: els.targetCell.value,
    fault_type: els.faultType.value,
    severity: Number(els.severity.value) / 100,
    network_load: Number(els.networkLoad.value) / 100,
    mobility: Number(els.mobility.value) / 100,
    weather_impact_override: Number(els.weather.value) / 100,
    healing_mode: els.healingMode.value,
  };
  await postJson("/api/fault", payload);
}

async function resetScenario() {
  await postJson("/api/reset", {});
}

async function applyTelemetry() {
  await postJson("/api/telemetry", {
    mode: els.telemetryMode.value,
    source: els.telemetrySource.value,
  });
}

async function postJson(url, payload) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`API ${response.status}`);
    applySnapshot(await response.json());
  } catch (error) {
    els.timeline.innerHTML = `<li>Backend request failed: ${escapeHtml(error.message)}</li>`;
  }
}

function renderMecNodes() {
  if (mecLayer.getLayers().length > 0) return;
  mecNodes.forEach((node) => {
    L.marker([node.lat, node.lon], {
      icon: L.divIcon({ className: "", html: `<div class="mec-marker"></div>`, iconSize: [18, 18] }),
    }).addTo(mecLayer).bindPopup(`<strong>${node.id}</strong><br>${node.site}`);
  });
}

function renderProfile(p, weather) {
  if (!p) return;
  const weatherLine = weather
    ? `${weather.mode === "live" ? "Live weather" : "Weather fallback"}: ${Math.round((weather.weather_impact || 0) * 100)}% impact`
    : "Weather: pending";
  els.profileDetails.innerHTML = `
    <strong>${escapeHtml(p.label)}</strong><br>
    Latency target: ${p.latency} ms<br>
    Jitter target: ${p.jitter} ms<br>
    Throughput target: ${p.throughput} Mbps<br>
    Reliability: ${p.reliability}%<br>
    Priority: ${p.priority}/6<br>
    Optimization: ${escapeHtml(p.weight)}<br>
    ${escapeHtml(weatherLine)}
  `;
  renderProfileMatrix(p.parameters || {});
}

function renderTelemetry(telemetry, sources) {
  if (!telemetry) return;
  if (telemetry.mode && els.telemetryMode.value !== telemetry.mode) els.telemetryMode.value = telemetry.mode;
  if (telemetry.source && els.telemetrySource.value !== telemetry.source) els.telemetrySource.value = telemetry.source;
  els.telemetryStatus.innerHTML = `
    <strong>${escapeHtml(telemetry.mode)}</strong><br>
    Adapter: ${escapeHtml(telemetry.adapter)}<br>
    OAI-ready schema: ${telemetry.oai_ready ? "yes" : "no"}<br>
    ${telemetry.watching ? "File watch: enabled<br>" : ""}
    ${telemetry.rows !== undefined ? `Rows: ${escapeHtml(telemetry.rows)}<br>` : ""}
    ${telemetry.source ? `Source: ${escapeHtml(telemetry.source)}<br>` : ""}
    ${escapeHtml(telemetry.next_integration || "")}
  `;
}

function renderLiveTelemetry(payload) {
  if (!payload || !els.liveTelemetryStatus || !els.liveTelemetryMatrix) return;
  const raw = payload.raw_runtime_log || {};
  const metrics = payload.live_metrics_log || {};
  const decisions = payload.live_decisions || {};
  const sqlite = payload.sqlite || {};
  els.liveTelemetryStatus.innerHTML = `
    <strong>${metrics.available ? "Metric stream available" : "Metric stream waiting"}</strong><br>
    Raw log lines: ${Number(raw.lines || 0).toLocaleString()}<br>
    Metric lines: ${Number(metrics.lines || 0).toLocaleString()}<br>
    Decision lines: ${Number(decisions.lines || 0).toLocaleString()}<br>
    SQLite live decisions: ${Number(sqlite.decisions || 0).toLocaleString()}<br>
    SQLite feature rows: ${Number(sqlite.feature_rows || 0).toLocaleString()}
  `;
  const recent = (sqlite.recent_decisions || []).slice(0, 5);
  els.liveTelemetryMatrix.innerHTML = recent.length
    ? recent.map((item) => `
      <p>
        <span>${escapeHtml(item.cell_id || "cell")}</span>
        <strong>${escapeHtml(item.root_cause || "normal")} / ${escapeHtml(item.healing_action || "no_action")}</strong>
      </p>
    `).join("")
    : "<p><span>Status</span><strong>No live decisions yet</strong></p>";
}

function renderPopulation(population) {
  if (!population) return;
  els.populationSummary.innerHTML = `
    <strong>${Number(population.totalDevices || 0).toLocaleString()} virtual devices</strong><br>
    Active now: ${Number(population.activeDevices || 0).toLocaleString()}<br>
    Estimated affected: ${Number(population.affectedDevices || 0).toLocaleString()}<br>
    Represented as service-level aggregates plus sample UEs.
  `;
  els.populationMatrix.innerHTML = Object.entries(population.byService || {})
    .map(([service, item]) => `
      <p>
        <span>${escapeHtml(service)}</span>
        <strong>${Number(item.totalDevices || 0).toLocaleString()} total / ${Number(item.affectedDevices || 0).toLocaleString()} affected</strong>
      </p>
    `)
    .join("");
}

function renderModelRegistry(registry) {
  if (!registry) return;
  const active = registry.active_models || {};
  els.modelRegistry.innerHTML = Object.entries(active)
    .map(([task, model]) => `<strong>${escapeHtml(task)}</strong>: ${escapeHtml(model)}`)
    .join("<br>");
}

function renderKpmDataset(dataset) {
  if (!dataset || !els.kpmDatasetSummary || !els.kpmDatasetMatrix) return;
  const train = dataset.trainingSummary || {};
  const aux = dataset.auxSummary || {};
  const benchmark = dataset.benchmark || {};
  const best = (benchmark.benchmarks || []).find((item) => item.name === "open_ran_kpm_self_learning_model");
  els.kpmDatasetSummary.innerHTML = [
    `Rows: <strong>${Number(train.rows_written || 0).toLocaleString()}</strong>`,
    `eMBB: <strong>${Number(train.service_class_counts?.eMBB || 0).toLocaleString()}</strong>`,
    `URLLC: <strong>${Number(train.service_class_counts?.URLLC || 0).toLocaleString()}</strong>`,
    `App QoS summaries: <strong>${Number(aux.application_qos_rows || 0).toLocaleString()}</strong>`,
    `Cell-load summaries: <strong>${Number(aux.cell_load_rows || 0).toLocaleString()}</strong>`,
  ].join("<br>");

  const sample = (dataset.trainingSamples || [])[0] || {};
  const appSample = (dataset.appQosSamples || [])[0] || {};
  const cellSample = (dataset.cellLoadSamples || [])[0] || {};
  const rows = [
    ["Source", "Open RAN commercial traffic twinning KPM"],
    ["Model F1", best ? best.f1_score : "not benchmarked"],
    ["Model recall", best ? best.recall : "not benchmarked"],
    ["Sample UE", sample.ue_id || "-"],
    ["Sample slice", sample.slice_id ? `slice ${sample.slice_id}, ${sample.slice_prb} PRBs` : "-"],
    ["Scheduler", sample.scheduling_policy || "-"],
    ["PRB grant ratio", sample.prb_grant_ratio || "-"],
    ["App delay", appSample.mean_app_delay_ms ? `${Number(appSample.mean_app_delay_ms).toFixed(2)} ms` : "-"],
    ["Cell load", cellSample.mean_connected_ues ? `${Number(cellSample.mean_connected_ues).toFixed(2)} UEs` : "-"],
  ];
  els.kpmDatasetMatrix.innerHTML = rows
    .map(([key, value]) => `<p><span>${escapeHtml(key)}</span><strong>${escapeHtml(value ?? "-")}</strong></p>`)
    .join("");
}

function renderProfileMatrix(params) {
  const rows = [
    ["QoS class", params.qos_class],
    ["Network slice", params.network_slice_type],
    ["Packet size", params.packet_size],
    ["Packet frequency", params.packet_frequency],
    ["Bandwidth", `${params.bandwidth_mhz} MHz`],
    ["Reliability", `${params.reliability_pct_target}%`],
    ["Availability", `${params.availability_pct_target}%`],
    ["Priority", params.resource_allocation_priority],
    ["Mobility", params.mobility_level],
    ["Connection density", params.connection_density],
    ["Device density", params.device_density],
    ["Error correction", params.error_correction_strength],
    ["Retransmission", params.retransmission_policy],
    ["Security", `L${params.security_level}, ${params.encryption_type}`],
    ["Authentication", params.authentication_strength],
    ["Power", params.power_consumption],
    ["Battery need", params.battery_life_requirement],
    ["Coverage", params.coverage_requirement],
    ["Handover", params.handover_sensitivity],
    ["Traffic", params.traffic_pattern],
    ["Burstiness", params.traffic_burstiness],
    ["Session", params.session_duration],
    ["Persistence", params.connection_persistence],
    ["Spectrum efficiency", params.spectrum_efficiency],
    ["Geo", params.geographic_distribution],
    ["Criticality", params.criticality_level],
    ["Scalability", params.scalability_requirement],
    ["Cost sensitivity", params.cost_sensitivity],
    ["Processing", params.processing_requirement],
    ["Edge dependency", params.edge_dependency_level],
    ["Fault tolerance", params.fault_tolerance_requirement],
    ["RTO", params.recovery_time_objective],
    ["Continuity", params.service_continuity_requirement],
    ["Regulatory", params.regulatory_constraints],
    ["Sync", params.synchronization_requirement],
  ];
  els.profileMatrix.innerHTML = rows
    .map(([key, value]) => `<p><span>${escapeHtml(key)}</span><strong>${escapeHtml(value ?? "-")}</strong></p>`)
    .join("");
}

function renderOutputs(selected, current, weather) {
  if (!selected || !current) return;
  els.clockLabel.textContent = `live t = ${state.t}s`;
  els.riskScore.textContent = Number(selected.risk).toFixed(2);
  els.slaStatus.textContent = selected.state === "fault" ? "Violation" : selected.state === "risk" ? "At risk" : "OK";
  els.postRisk.textContent = Number(selected.validation.postRisk).toFixed(2);
  els.automationSafety.textContent = Number(selected.automationSafety?.score ?? 1).toFixed(2);
  els.safetyDecision.textContent = selected.automationSafety?.decision || "monitor_only";
  els.predictiveHorizon.textContent = selected.prediction?.horizon || "stable";
  els.aiTrust.textContent = Number(selected.security?.aiTrustScore ?? 1).toFixed(2);
  els.amlThreat.textContent = selected.security?.amlThreatLevel || "low";
  els.driftStatus.textContent = selected.drift?.status || "warming_up";
  els.driftScore.textContent = Number(selected.drift?.score ?? 0).toFixed(2);
  els.xappConflict.textContent = selected.xappConflict?.detected ? selected.xappConflict.type : "none";
  els.selectedXapp.textContent = selected.xappConflict?.selectedXapp || "self_healing_xapp";
  els.slaImpact.textContent = selected.sliceImpact?.level || "none";
  els.timingState.textContent = selected.timing?.state || "stable";
  els.spectrumState.textContent = selected.spectrum?.state || "spectrum_stable";
  els.spectrumRisk.textContent = Number(selected.spectrum?.riskScore ?? 0).toFixed(2);
  els.rootCause.textContent = selected.rootCause;
  els.confidence.textContent = `${Math.round(selected.confidence * 100)}%`;
  els.healingAction.textContent = selected.healingAction;
  els.baselineAction.textContent = selected.automationSafety?.baselineWouldExecute ? "execute" : "hold";
  els.guardedAction.textContent = selected.automationSafety?.guardedWouldExecute ? "execute" : "hold";
  els.safetyImprovement.textContent = selected.automationSafety?.unsafeActionPrevented
    ? "unsafe baseline action prevented"
    : selected.automationSafety?.improvement || "monitoring only";
  els.validation.textContent = selected.validation.approved ? "Approved" : "Blocked";
  els.securityGuard.textContent = selected.security?.guardAction || "allow_automation";
  els.threatType.textContent = selected.security?.amlThreatType || "none";
  els.driftType.textContent = selected.drift?.type || "none";
  els.modelAction.textContent = selected.drift?.adaptationAction || "collect_more_samples";
  els.conflictStrategy.textContent = selected.xappConflict?.mitigationStrategy || "no_conflict";
  els.policyState.textContent = selected.policy?.state || "policy_allow";
  els.spectrumAction.textContent = selected.spectrum?.action || "maintain_current_radio_policy";
  els.customerImpact.textContent = selected.sliceImpact?.customerImpact || "no_visible_impact";
  renderUeSamples(current.devicePopulation?.representativeUes || []);
  renderOpenRanReplayRow(selected.openRanKpm);

  els.overallState.className = `status-pill ${selected.state}`;
  els.overallState.textContent = selected.state === "fault" ? "Fault" : selected.state === "risk" ? "At risk" : "Healthy";

  const k = selected.kpis;
  const items = [
    ["Latency", `${k.latency.toFixed(2)} ms`],
    ["Jitter", `${k.jitter.toFixed(2)} ms`],
    ["Throughput", `${k.throughput.toFixed(2)} Mbps`],
    ["Packet loss", `${k.loss.toFixed(3)}%`],
    ["PRB use", `${k.prb.toFixed(1)}%`],
    ["Handover fail", `${k.handover.toFixed(2)}%`],
    ["Edge delay", `${k.edgeDelay.toFixed(2)} ms`],
    ["Backhaul delay", `${k.backhaul.toFixed(2)} ms`],
    ["SINR", `${k.sinr.toFixed(2)} dB`],
    ["BLER", `${k.bler.toFixed(2)}%`],
  ];
  els.kpiGrid.innerHTML = items.map(([key, value]) => `<div class="kpi"><span>${key}</span><strong>${value}</strong></div>`).join("");

  const weatherText = weather?.mode === "live"
    ? `Open-Meteo live Bengaluru weather: rain ${weather.rain} mm, wind ${weather.wind_speed_10m} km/h.`
    : `Open-Meteo unavailable; using conservative weather impact ${Math.round((weather?.weather_impact || 0.1) * 100)}%.`;
  els.timeline.innerHTML = [
    `Backend live tick ${state.t} evaluated ${selected.id} (${selected.site}) for ${current.service}.`,
    weatherText,
    `Digital Twin risk score: ${Number(selected.risk).toFixed(2)}; SLA state: ${selected.state}.`,
    `Device population: ${Number(current.devicePopulation?.totalDevices || 0).toLocaleString()} virtual devices represented; ${Number(current.devicePopulation?.affectedDevices || 0).toLocaleString()} estimated affected.`,
    `Automation safety: ${Number(selected.automationSafety?.score ?? 1).toFixed(2)}; ${selected.automationSafety?.decision || "monitor_only"}; baseline ${selected.automationSafety?.baselineWouldExecute ? "execute" : "hold"} -> guarded ${selected.automationSafety?.guardedWouldExecute ? "execute" : "hold"}.`,
    `Slice twin: ${selected.sliceImpact?.sliceId || "slice_unknown"}; breach probability ${Number(selected.sliceImpact?.slaBreachProbability ?? 0).toFixed(2)}; action ${selected.sliceImpact?.recommendedAction || "maintain_slice_policy"}.`,
    `RCA result: ${selected.rootCause}; confidence ${Math.round(selected.confidence * 100)}%.`,
    `xApp distillation: ${selected.xappConflict?.mitigationStrategy || "no_conflict"}; selected ${selected.xappConflict?.selectedXapp || "self_healing_xapp"} for ${selected.xappConflict?.distillationState || "unknown_state"}.`,
    `Drift lifecycle: ${selected.drift?.lifecycleStage || "baseline_initialization"}; ${selected.drift?.automationMode || "monitor_only"}; action ${selected.drift?.adaptationAction || "collect_more_samples"}.`,
    `AML guard: ${selected.security?.guardAction || "allow_automation"}; AI trust ${Number(selected.security?.aiTrustScore ?? 1).toFixed(2)}; threat ${selected.security?.amlThreatType || "none"}.`,
    `AML attack injection: ${selected.amlAttack?.active ? selected.amlAttack.type : "none"}.`,
    `Timing twin: ${selected.timing?.syncState || "synchronized"} in ${selected.timing?.ptpDomain || "ptp_domain_unknown"}; STRIDE test ${selected.timing?.strideTestCase || "ptp_baseline_sync_health_check"}.`,
    `ZSM policy: ${selected.policy?.zsmWorkflowStage || "detect_decide_execute_record"}; escalation ${selected.policy?.escalationLevel || "auto_record"}; audit ${selected.policy?.auditEventId || "audit_pending"}.`,
    `DTN readiness: ${selected.digitalTwinNetwork?.state || "not_ready"} (${Number(selected.digitalTwinNetwork?.readinessScore ?? 0).toFixed(2)}); mode ${selected.digitalTwinNetwork?.orchestrationMode || "monitor_only"}.`,
    `Spectrum DSA: ${selected.spectrum?.dsaPolicy || "hold_current_channel"} on ${selected.spectrum?.channel || "unknown_channel"}; source ${selected.spectrum?.interferenceSource || "none"}.`,
    `Prediction: ${selected.prediction?.horizon || "stable"}; watch ${selected.prediction?.watchItem || "normal"}.`,
    `Healing: ${selected.healingAction}; validation: ${selected.validation.note}`,
  ].map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderOpenRanReplayRow(row) {
  if (!els.openRanReplayRow) return;
  if (!row) {
    els.openRanReplayRow.innerHTML = "<p><span>Status</span><strong>not using Open RAN KPM replay</strong></p>";
    return;
  }
  const rows = [
    ["UE", row.ueId || "-"],
    ["Service", row.serviceClass || "-"],
    ["Inferred fault", `${row.faultType || "normal"} (${row.labelQuality || "unlabelled"})`],
    ["Slice", `slice ${row.sliceId || "-"}, ${row.slicePrb || "-"} PRBs`],
    ["Scheduler", row.schedulingPolicy || "-"],
    ["PRB grant ratio", row.prbGrantRatio || "-"],
    ["CQI / MCS", `${row.dlCqi || "-"} / DL ${row.dlMcs || "-"} / UL ${row.ulMcs || "-"}`],
    ["Experiment", `${row.cluster || "-"} / ${row.slicing || "-"} / ${row.scheduling || "-"}`],
    ["Reservation", row.reservation || "-"],
  ];
  els.openRanReplayRow.innerHTML = rows
    .map(([key, value]) => `<p><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></p>`)
    .join("");
}

function renderOpenRanUeView(history) {
  if (!els.openRanUeChart || !els.openRanUeTable) return;
  const rows = history
    .map((item) => item?.selected)
    .filter((selected) => selected?.openRanKpm)
    .slice(-12);
  if (!rows.length) {
    els.openRanUeChart.innerHTML = "<div class=\"empty-chart\">Switch telemetry to Open RAN KPM replay.</div>";
    els.openRanUeTable.innerHTML = "<tr><td colspan=\"6\">No Open RAN replay rows yet.</td></tr>";
    return;
  }
  const maxPrb = Math.max(1, ...rows.map((row) => Number(row.kpis?.prb || 0)));
  els.openRanUeChart.innerHTML = rows.map((row) => {
    const kpm = row.openRanKpm;
    const prb = Number(row.kpis?.prb || 0);
    const width = Math.max(4, Math.round((prb / maxPrb) * 100));
    const cls = row.fault && row.fault !== "normal" ? "fault" : "normal";
    return `
      <div class="ue-bar-row">
        <span>${escapeHtml(kpm.ueId || "-")}</span>
        <div class="ue-bar-track"><i class="${cls}" style="width:${width}%"></i></div>
        <strong>${prb.toFixed(0)}%</strong>
      </div>
    `;
  }).join("");
  els.openRanUeTable.innerHTML = rows.slice(-8).reverse().map((row) => {
    const kpm = row.openRanKpm;
    return `
      <tr>
        <td>${escapeHtml(kpm.ueId || "-")}</td>
        <td>${escapeHtml(kpm.sliceId || "-")}</td>
        <td>${escapeHtml(formatRatio(kpm.prbGrantRatio))}</td>
        <td>${Number(row.kpis?.sinr ?? 0).toFixed(1)}</td>
        <td>${Number(row.kpis?.prb ?? 0).toFixed(0)}%</td>
        <td>${escapeHtml(kpm.faultType || "normal")}</td>
      </tr>
    `;
  }).join("");
}

function renderUeSamples(samples) {
  if (!samples.length) {
    els.ueSamples.innerHTML = "<p>No UE samples available.</p>";
    return;
  }
  els.ueSamples.innerHTML = samples.map((ue) => `
    <div class="ue-item ${escapeHtml(ue.state)}">
      <strong>${escapeHtml(ue.ueId)}</strong>
      <span>${escapeHtml(ue.service)} / ${escapeHtml(ue.deviceType)} / risk ${Number(ue.risk || 0).toFixed(2)}</span>
    </div>
  `).join("");
}

function renderCells(cellResults) {
  cellLayer.clearLayers();
  cellResults.forEach((cell) => {
    const selected = cell.selected ? " selected" : "";
    const marker = L.marker([cell.lat, cell.lon], {
      icon: L.divIcon({ className: "", html: `<div class="cell-marker ${cell.state}${selected}"></div>`, iconSize: [22, 22] }),
    }).addTo(cellLayer);
    marker.bindPopup(
      `<strong>${escapeHtml(cell.id)}</strong><br>${escapeHtml(cell.site)}<br>` +
      `Edge: ${escapeHtml(cell.edge)}<br>Status: ${escapeHtml(cell.state)}<br>` +
      `Risk: ${Number(cell.risk).toFixed(2)}<br>AI trust: ${Number(cell.security?.aiTrustScore ?? 1).toFixed(2)}<br>` +
      `Safety: ${Number(cell.automationSafety?.score ?? 1).toFixed(2)} (${escapeHtml(cell.automationSafety?.decision || "monitor_only")})<br>` +
      `AML: ${escapeHtml(cell.security?.amlThreatLevel || "low")}<br>Drift: ${escapeHtml(cell.drift?.status || "warming_up")}<br>` +
      `xApp conflict: ${escapeHtml(cell.xappConflict?.type || "none")}<br>` +
      `Spectrum: ${escapeHtml(cell.spectrum?.state || "spectrum_stable")}<br>` +
      `SLA impact: ${escapeHtml(cell.sliceImpact?.level || "none")}<br>` +
      `RCA: ${escapeHtml(cell.rootCause)}`
    );
    marker.on("click", () => {
      els.targetCell.value = cell.id;
      applyScenario();
    });
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function formatRatio(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "-";
}

init();
