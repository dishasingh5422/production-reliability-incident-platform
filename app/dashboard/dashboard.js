const state = {
  data: null,
  filter: "all",
  refreshTimer: null,
};

const elements = {
  banner: document.querySelector("#connection-banner"),
  refreshButton: document.querySelector("#refresh-button"),
  lastUpdated: document.querySelector("#last-updated"),
  environment: document.querySelector("#sidebar-environment"),
  hero: document.querySelector(".status-hero"),
  serviceHeading: document.querySelector("#service-heading"),
  serviceDetail: document.querySelector("#service-detail"),
  liveLabel: document.querySelector("#live-label"),
  availability: document.querySelector("#availability-value"),
  availabilityNote: document.querySelector("#availability-note"),
  latency: document.querySelector("#latency-value"),
  incidentValue: document.querySelector("#incident-value"),
  incidentNote: document.querySelector("#incident-note"),
  mttr: document.querySelector("#mttr-value"),
  chart: document.querySelector("#latency-chart"),
  deploymentStatus: document.querySelector("#deployment-status"),
  deploymentVersion: document.querySelector("#deployment-version"),
  deploymentEnvironment: document.querySelector("#deployment-environment"),
  deploymentCommit: document.querySelector("#deployment-commit"),
  deploymentTime: document.querySelector("#deployment-time"),
  incidentSummary: document.querySelector("#incident-summary"),
  incidentList: document.querySelector("#incident-list"),
  checksBody: document.querySelector("#checks-body"),
};

function formatNumber(value, suffix = "") {
  if (value === null || value === undefined) return "—";
  return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}${suffix}`;
}

function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.round(seconds % 60);
  return `${minutes}m ${remaining}s`;
}

function formatDate(value, compact = false) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, compact
    ? { hour: "2-digit", minute: "2-digit", second: "2-digit" }
    : { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }
  ).format(date);
}

function setText(element, value) {
  element.textContent = value;
}

function statusClass(value) {
  return String(value || "neutral").toLowerCase().replaceAll("_", "-");
}

function pill(text, className = "status-pill") {
  const span = document.createElement("span");
  span.className = `${className} ${statusClass(text)}`;
  span.textContent = text || "Unknown";
  return span;
}

function renderOverview(data) {
  const operational = data.state === "operational";
  elements.hero.classList.toggle("degraded", !operational);
  setText(elements.serviceHeading, operational ? "All systems operational" : "Service degradation detected");
  const detail = operational
    ? `${data.service} · version ${data.version}`
    : `${data.service} · controlled ${data.fault_mode || "unknown"} condition`;
  setText(elements.serviceDetail, detail);
  setText(elements.liveLabel, operational ? "Live" : "Attention");
  setText(elements.environment, data.environment);

  setText(elements.availability, formatNumber(data.check_pass_rate_percent, "%"));
  setText(
    elements.availabilityNote,
    data.check_pass_rate_percent === null ? "No qualifying checks in this window" : `${data.window_hours}-hour synthetic-check window`,
  );
  setText(elements.latency, data.average_response_ms === null ? "—" : `${formatNumber(data.average_response_ms)} ms`);
  setText(elements.incidentValue, String(data.open_incidents));
  const severity = data.open_incidents_by_severity;
  setText(elements.incidentNote, `${severity.HIGH} high · ${severity.MEDIUM} medium · ${severity.LOW} low`);
  setText(elements.mttr, formatDuration(data.average_mttr_seconds));
}

function renderLatencyChart(checks) {
  const timed = checks
    .filter((check) => check.response_ms !== null && check.response_ms !== undefined)
    .slice(0, 18)
    .reverse();
  elements.chart.replaceChildren();
  if (timed.length < 2) {
    const empty = document.createElement("div");
    empty.className = "chart-empty";
    empty.textContent = "Two timed monitoring observations are needed for the trend.";
    elements.chart.append(empty);
    return;
  }

  const width = 760;
  const height = 236;
  const padding = { top: 18, right: 16, bottom: 30, left: 46 };
  const values = timed.map((check) => Number(check.response_ms));
  const maxValue = Math.max(...values, 10) * 1.15;
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const points = values.map((value, index) => ({
    x: padding.left + (index / (values.length - 1)) * plotWidth,
    y: padding.top + plotHeight - (value / maxValue) * plotHeight,
  }));
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
  const areaPath = `${path} L ${points.at(-1).x.toFixed(1)} ${padding.top + plotHeight} L ${points[0].x.toFixed(1)} ${padding.top + plotHeight} Z`;
  const svgNamespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNamespace, "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("aria-hidden", "true");

  const defs = document.createElementNS(svgNamespace, "defs");
  const gradient = document.createElementNS(svgNamespace, "linearGradient");
  gradient.setAttribute("id", "latency-fill");
  gradient.setAttribute("x1", "0");
  gradient.setAttribute("y1", "0");
  gradient.setAttribute("x2", "0");
  gradient.setAttribute("y2", "1");
  [["0%", "0.24"], ["100%", "0"]].forEach(([offset, opacity]) => {
    const stop = document.createElementNS(svgNamespace, "stop");
    stop.setAttribute("offset", offset);
    stop.setAttribute("stop-color", "#53d8ff");
    stop.setAttribute("stop-opacity", opacity);
    gradient.append(stop);
  });
  defs.append(gradient);
  svg.append(defs);

  [0, 0.5, 1].forEach((ratio) => {
    const y = padding.top + plotHeight * ratio;
    const line = document.createElementNS(svgNamespace, "line");
    line.setAttribute("x1", String(padding.left));
    line.setAttribute("x2", String(width - padding.right));
    line.setAttribute("y1", String(y));
    line.setAttribute("y2", String(y));
    line.setAttribute("class", "chart-grid-line");
    svg.append(line);

    const label = document.createElementNS(svgNamespace, "text");
    label.setAttribute("x", "3");
    label.setAttribute("y", String(y + 4));
    label.setAttribute("class", "chart-label");
    label.textContent = `${Math.round(maxValue * (1 - ratio))}ms`;
    svg.append(label);
  });

  const area = document.createElementNS(svgNamespace, "path");
  area.setAttribute("d", areaPath);
  area.setAttribute("class", "chart-area");
  svg.append(area);
  const line = document.createElementNS(svgNamespace, "path");
  line.setAttribute("d", path);
  line.setAttribute("class", "chart-line");
  svg.append(line);
  points.forEach((point, index) => {
    const circle = document.createElementNS(svgNamespace, "circle");
    circle.setAttribute("cx", String(point.x));
    circle.setAttribute("cy", String(point.y));
    circle.setAttribute("r", index === points.length - 1 ? "4" : "2.5");
    circle.setAttribute("class", "chart-point");
    svg.append(circle);
  });
  const firstLabel = document.createElementNS(svgNamespace, "text");
  firstLabel.setAttribute("x", String(padding.left));
  firstLabel.setAttribute("y", String(height - 5));
  firstLabel.setAttribute("class", "chart-label");
  firstLabel.textContent = formatDate(timed[0].checked_at, true);
  svg.append(firstLabel);
  const lastLabel = document.createElementNS(svgNamespace, "text");
  lastLabel.setAttribute("x", String(width - padding.right));
  lastLabel.setAttribute("y", String(height - 5));
  lastLabel.setAttribute("text-anchor", "end");
  lastLabel.setAttribute("class", "chart-label");
  lastLabel.textContent = formatDate(timed.at(-1).checked_at, true);
  svg.append(lastLabel);
  elements.chart.append(svg);
}

function renderDeployment(deployment, data) {
  if (!deployment) {
    elements.deploymentStatus.className = "badge neutral";
    setText(elements.deploymentStatus, "Local runtime");
    setText(elements.deploymentVersion, data.version);
    setText(elements.deploymentEnvironment, data.environment);
    setText(elements.deploymentCommit, "Not recorded");
    setText(elements.deploymentTime, "Current session");
    return;
  }
  const successful = ["SUCCESS", "SUCCEEDED", "DEPLOYED"].includes(deployment.status);
  elements.deploymentStatus.className = `badge ${successful ? "success" : "neutral"}`;
  setText(elements.deploymentStatus, deployment.status);
  setText(elements.deploymentVersion, deployment.version);
  setText(elements.deploymentEnvironment, deployment.environment);
  setText(elements.deploymentCommit, deployment.commit_sha.slice(0, 10));
  elements.deploymentCommit.title = deployment.commit_sha;
  setText(elements.deploymentTime, formatDate(deployment.started_at));
}

function renderIncidents(incidents) {
  elements.incidentList.replaceChildren();
  const openCount = incidents.filter((incident) => ["OPEN", "ACKNOWLEDGED"].includes(incident.status)).length;
  setText(elements.incidentSummary, `${incidents.length} shown · ${openCount} open`);
  if (!incidents.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    const icon = document.createElement("span");
    icon.textContent = "✓";
    const message = document.createElement("strong");
    message.textContent = "No incident history recorded";
    empty.append(icon, message);
    elements.incidentList.append(empty);
    return;
  }
  incidents.forEach((incident) => {
    const row = document.createElement("div");
    row.className = "incident-row";
    const identity = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = incident.short_description;
    const reference = document.createElement("small");
    reference.textContent = incident.external_incident_id || `Local incident ${incident.id}`;
    identity.append(title, reference);
    const detected = document.createElement("div");
    const detectedValue = document.createElement("strong");
    detectedValue.textContent = formatDate(incident.detected_at);
    const detectedLabel = document.createElement("small");
    detectedLabel.textContent = "Detected";
    detected.append(detectedValue, detectedLabel);
    const source = document.createElement("div");
    const sourceValue = document.createElement("strong");
    sourceValue.textContent = incident.detection_source.replaceAll("-", " ");
    const sourceLabel = document.createElement("small");
    sourceLabel.textContent = incident.resolved_at ? `Resolved ${formatDate(incident.resolved_at)}` : "Active signal";
    source.append(sourceValue, sourceLabel);
    const labels = document.createElement("div");
    labels.append(pill(incident.severity, "severity-pill"), pill(incident.status));
    labels.style.display = "flex";
    labels.style.gap = "6px";
    labels.style.flexWrap = "wrap";
    row.append(identity, detected, source, labels);
    elements.incidentList.append(row);
  });
}

function shouldShowCheck(check) {
  if (state.filter === "healthy") return check.status === "HEALTHY";
  if (state.filter === "failed") return ["FAILED", "CRITICAL", "WARNING"].includes(check.status);
  return true;
}

function renderChecks(checks) {
  elements.checksBody.replaceChildren();
  const visible = checks.filter(shouldShowCheck).slice(0, 16);
  if (!visible.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.className = "table-empty";
    cell.textContent = "No checks match this view.";
    row.append(cell);
    elements.checksBody.append(row);
    return;
  }
  visible.forEach((check) => {
    const row = document.createElement("tr");
    const statusCell = document.createElement("td");
    statusCell.append(pill(check.status));
    const typeCell = document.createElement("td");
    typeCell.textContent = check.check_type.replaceAll("-", " ");
    const targetCell = document.createElement("td");
    targetCell.className = "target";
    targetCell.textContent = check.target;
    targetCell.title = check.target;
    const responseCell = document.createElement("td");
    responseCell.className = "mono";
    responseCell.textContent = check.response_ms === null ? "—" : `${formatNumber(check.response_ms)} ms`;
    const httpCell = document.createElement("td");
    httpCell.className = "mono";
    httpCell.textContent = check.status_code || "—";
    const timeCell = document.createElement("td");
    timeCell.className = "mono";
    timeCell.textContent = formatDate(check.checked_at);
    row.append(statusCell, typeCell, targetCell, responseCell, httpCell, timeCell);
    elements.checksBody.append(row);
  });
}

function render(data) {
  state.data = data;
  renderOverview(data);
  renderLatencyChart(data.recent_checks);
  renderDeployment(data.latest_deployment, data);
  renderIncidents(data.recent_incidents);
  renderChecks(data.recent_checks);
  setText(elements.lastUpdated, `Updated ${formatDate(data.generated_at, true)}`);
}

async function refreshDashboard() {
  elements.refreshButton.classList.add("loading");
  elements.refreshButton.disabled = true;
  try {
    await fetch("/readyz", { headers: { Accept: "application/json" }, cache: "no-store" });
    const response = await fetch("/api/dashboard", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`Dashboard request returned ${response.status}`);
    render(await response.json());
    elements.banner.hidden = true;
  } catch (error) {
    console.error(error);
    elements.banner.hidden = false;
    setText(elements.lastUpdated, "Connection interrupted");
  } finally {
    elements.refreshButton.classList.remove("loading");
    elements.refreshButton.disabled = false;
  }
}

document.querySelectorAll(".filter-chip").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll(".filter-chip").forEach((chip) => chip.classList.toggle("active", chip === button));
    if (state.data) renderChecks(state.data.recent_checks);
  });
});

elements.refreshButton.addEventListener("click", refreshDashboard);
refreshDashboard();
state.refreshTimer = window.setInterval(refreshDashboard, 15000);
