const DATA = Array.isArray(window.GEOTURISMO_DATA) ? window.GEOTURISMO_DATA : [];
const ATTRACTIONS = Array.isArray(window.GEOTURISMO_ATTRACTIONS) ? window.GEOTURISMO_ATTRACTIONS : [];
const TYPE_SUMMARY = Array.isArray(window.GEOTURISMO_TYPE_SUMMARY) ? window.GEOTURISMO_TYPE_SUMMARY : [];

const fmt = (value, decimals = 0) => Number(value || 0).toLocaleString("es-CO", {
  maximumFractionDigits: decimals,
  minimumFractionDigits: decimals
});

function years() {
  const set = new Set();
  DATA.forEach((item) => Object.keys(item.visitantes || {}).forEach((year) => set.add(Number(year))));
  return [...set].filter(Boolean).sort((a, b) => a - b);
}

function selectedYear() {
  return document.getElementById("year-select").value;
}

function selectedType() {
  return document.getElementById("type-select").value;
}

function selectedMunicipality() {
  return document.getElementById("municipality-select").value;
}

function selectedMetric() {
  return document.getElementById("metric-select").value;
}

function valueFor(item, variable, year) {
  return Number((item[variable] || {})[year] || 0);
}

function populateYearSelect() {
  const select = document.getElementById("year-select");
  const available = years();
  const latest = available[available.length - 1] || new Date().getFullYear();
  select.innerHTML = available.map((year) => (
    `<option value="${year}" ${year === latest ? "selected" : ""}>${year}</option>`
  )).join("");
}

function populateTypeSelect() {
  const select = document.getElementById("type-select");
  const types = typeCounts().map((item) => item.name);
  select.innerHTML = [
    '<option value="todos">Todos</option>',
    ...types.map((type) => `<option value="${type}">${type}</option>`)
  ].join("");
}

function populateMunicipalitySelect() {
  const select = document.getElementById("municipality-select");
  const municipalities = [...new Set([
    ...DATA.map((item) => item.municipio),
    ...ATTRACTIONS.map((item) => item.municipio)
  ].filter(Boolean))].sort((a, b) => a.localeCompare(b, "es"));
  select.innerHTML = [
    '<option value="todos">Todos</option>',
    ...municipalities.map((municipality) => `<option value="${municipality}">${municipality}</option>`)
  ].join("");
}

function filteredAttractions() {
  const type = selectedType();
  const municipality = selectedMunicipality();
  return ATTRACTIONS.filter((item) => {
    const matchType = type === "todos" || item.tipo_turismo === type || item.tipo_secundario === type;
    const matchMunicipality = municipality === "todos" || item.municipio === municipality;
    return matchType && matchMunicipality;
  });
}

function filteredData() {
  const type = selectedType();
  const municipality = selectedMunicipality();
  const attractionMunicipalities = new Set(filteredAttractions().map((item) => item.municipio));
  return DATA.filter((item) => {
    const matchMunicipality = municipality === "todos" || item.municipio === municipality;
    const matchType = type === "todos"
      || item.tipo_predominante === type
      || (Array.isArray(item.tipos_turismo) && item.tipos_turismo.includes(type))
      || attractionMunicipalities.has(item.municipio);
    return matchMunicipality && matchType;
  });
}

function typeCounts() {
  const municipality = document.getElementById("municipality-select")?.value || "todos";
  const source = municipality === "todos"
    ? ATTRACTIONS
    : ATTRACTIONS.filter((item) => item.municipio === municipality);
  const counts = {};
  source.forEach((item) => {
    const type = item.tipo_turismo || "Sin clasificar";
    counts[type] = (counts[type] || 0) + 1;
  });
  const calculated = Object.entries(counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
  if (calculated.length) return calculated;
  if (TYPE_SUMMARY.length) {
    return TYPE_SUMMARY.map((item) => ({
      name: item.tipo_turismo,
      value: Number(item.atractivos || 0)
    })).sort((a, b) => b.value - a.value);
  }
  return [];
}

function municipalityAttractionCounts() {
  const source = filteredAttractions();
  const counts = {};
  source.forEach((item) => {
    const name = item.municipio || "Sin municipio";
    counts[name] = (counts[name] || 0) + 1;
  });
  return Object.entries(counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
}

function visitorsByYear() {
  const source = filteredData();
  return years().map((year) => ({
    year,
    value: source.reduce((acc, item) => acc + valueFor(item, "visitantes", year), 0)
  }));
}

function opportunityRanking(year) {
  return filteredData()
    .map((item) => ({ name: item.municipio, value: valueFor(item, "oportunidad", year) }))
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);
}

function renderKpis(year) {
  const types = typeCounts();
  const attractions = filteredAttractions();
  const data = filteredData();
  const municipalities = new Set(attractions.map((item) => item.municipio).filter(Boolean));
  const totalVisitors = data.reduce((acc, item) => acc + valueFor(item, "visitantes", year), 0);
  const subtitle = `Valle del Cauca · ${fmt(totalVisitors)} visitantes · ${fmt(data.length)} municipios filtrados`;

  document.getElementById("panel-subtitle").textContent = subtitle;
  document.getElementById("kpi-attractions").textContent = fmt(attractions.length);
  document.getElementById("kpi-types").textContent = fmt(types.length);
  document.getElementById("kpi-municipalities").textContent = fmt(municipalities.size);
  document.getElementById("kpi-top-type").textContent = types[0] ? types[0].name : "-";
  document.getElementById("kpi-top-type-sub").textContent = types[0] ? `${fmt(types[0].value)} atractivos registrados` : "sin datos";
}

function renderYearBars(year) {
  const series = visitorsByYear();
  const max = Math.max(...series.map((item) => item.value), 1);
  const container = document.getElementById("year-bars");
  container.style.setProperty("--bars", Math.max(series.length, 1));
  container.innerHTML = series.map((item) => {
    const height = Math.max(3, (item.value / max) * 100);
    return `<div class="year-bar ${String(item.year) === String(year) ? "active" : ""}" title="${fmt(item.value)} visitantes">
      <div style="height:${height}%"></div>
      <span>${item.year}</span>
    </div>`;
  }).join("");

  const selected = series.find((item) => String(item.year) === String(year));
  document.getElementById("visitors-total").textContent = `${fmt(selected ? selected.value : 0)} visitantes`;
}

function renderRank(containerId, rows, formatter = (value) => fmt(value)) {
  const container = document.getElementById(containerId);
  const top = rows.slice(0, 6);
  const max = Math.max(...top.map((item) => item.value), 1);
  container.innerHTML = top.map((item) => {
    const width = Math.max(2, (item.value / max) * 100);
    return `<div class="rank-row">
      <span title="${item.name}">${item.name}</span>
      <div class="rank-track"><div class="rank-fill" style="width:${width}%"></div></div>
      <b>${formatter(item.value)}</b>
    </div>`;
  }).join("");
}

function renderDashboard() {
  const year = selectedYear();
  const metric = selectedMetric();
  renderKpis(year);
  renderYearBars(year);
  renderRank("top-municipalities", municipalityAttractionCounts(), (value) => `${fmt(value)} atr.`);
  renderRank("type-bars", typeCounts(), (value) => `${fmt(value)} atr.`);
  const ranking = metric === "atractivos"
    ? municipalityAttractionCounts()
    : filteredData()
      .map((item) => ({ name: item.municipio, value: valueFor(item, metric, year) }))
      .filter((item) => item.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);
  const metricFormat = metric === "oportunidad" ? (value) => fmt(value, 2) : (value) => fmt(value);
  renderRank("opportunity-ranking", ranking, metricFormat);
  const metricLabels = {
    atractivos: "atractivos",
    visitantes: "visitantes",
    oportunidad: "indice de oportunidad",
    gasto: "gasto estimado"
  };
  document.querySelector("#priorizacion .chart-title span").textContent = metricLabels[metric] || "metrica";

  const available = years();
  const index = available.indexOf(Number(year));
  const progress = available.length > 1 ? ((index + 1) / available.length) * 100 : 80;
  document.getElementById("year-progress").style.width = `${progress}%`;
}

populateYearSelect();
populateTypeSelect();
populateMunicipalitySelect();
document.getElementById("year-select").addEventListener("change", renderDashboard);
document.getElementById("type-select").addEventListener("change", renderDashboard);
document.getElementById("municipality-select").addEventListener("change", renderDashboard);
document.getElementById("metric-select").addEventListener("change", renderDashboard);
renderDashboard();
