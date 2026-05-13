const DATA = Array.isArray(window.GEOTURISMO_DATA) ? window.GEOTURISMO_DATA : [];
const ATTRACTIONS = Array.isArray(window.GEOTURISMO_ATTRACTIONS) ? window.GEOTURISMO_ATTRACTIONS : [];

const fmt = (value, decimals = 0) => Number(value || 0).toLocaleString("es-CO", {
  maximumFractionDigits: decimals,
  minimumFractionDigits: decimals
});

function years() {
  const set = new Set();
  DATA.forEach((item) => Object.keys(item.visitantes || {}).forEach((year) => set.add(Number(year))));
  return [...set].filter(Boolean).sort((a, b) => a - b);
}

function valueFor(item, variable, year) {
  return Number((item[variable] || {})[year] || 0);
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

function populateFilters() {
  const yearSelect = document.getElementById("year-select");
  const availableYears = years();
  const latest = availableYears[availableYears.length - 1] || new Date().getFullYear();
  yearSelect.innerHTML = availableYears.map((year) => (
    `<option value="${year}" ${year === latest ? "selected" : ""}>${year}</option>`
  )).join("");

  const types = [...new Set(ATTRACTIONS.flatMap((item) => [item.tipo_turismo, item.tipo_secundario]).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, "es"));
  document.getElementById("type-select").innerHTML = [
    '<option value="todos">Todos</option>',
    ...types.map((type) => `<option value="${type}">${type}</option>`)
  ].join("");

  const municipalities = [...new Set([...DATA.map((item) => item.municipio), ...ATTRACTIONS.map((item) => item.municipio)].filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, "es"));
  document.getElementById("municipality-select").innerHTML = [
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
  const municipalitiesByType = new Set(filteredAttractions().map((item) => item.municipio));
  return DATA.filter((item) => {
    const matchMunicipality = municipality === "todos" || item.municipio === municipality;
    const matchType = type === "todos"
      || item.tipo_predominante === type
      || (Array.isArray(item.tipos_turismo) && item.tipos_turismo.includes(type))
      || municipalitiesByType.has(item.municipio);
    return matchMunicipality && matchType;
  });
}

function aggregateByYear(variable) {
  const source = filteredData();
  return years().map((year) => {
    const values = source.map((item) => valueFor(item, variable, year));
    const sum = values.reduce((acc, value) => acc + value, 0);
    return {
      year,
      value: variable === "oportunidad" ? sum / (values.length || 1) : sum
    };
  });
}

function typeCounts() {
  const counts = {};
  filteredAttractions().forEach((item) => {
    const type = item.tipo_turismo || "Sin clasificar";
    counts[type] = (counts[type] || 0) + 1;
  });
  return Object.entries(counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
}

function rankBy(variable, year) {
  return filteredData()
    .map((item) => ({ name: item.municipio, value: valueFor(item, variable, year) }))
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);
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

function renderBars() {
  const series = aggregateByYear("visitantes");
  const max = Math.max(...series.map((item) => item.value), 1);
  const selected = selectedYear();
  const container = document.getElementById("indicator-bars");
  container.style.setProperty("--bars", Math.max(series.length, 1));
  container.innerHTML = series.map((item) => {
    const height = Math.max(3, (item.value / max) * 100);
    return `<div class="year-bar ${String(item.year) === String(selected) ? "active" : ""}">
      <div style="height:${height}%"></div>
      <span>${item.year}</span>
    </div>`;
  }).join("");
  const current = series.find((item) => String(item.year) === String(selected));
  document.getElementById("indicator-total").textContent = `${fmt(current ? current.value : 0)} visitantes`;
}

function renderIndicators() {
  const year = selectedYear();
  const data = filteredData();
  const attractions = filteredAttractions();
  const visitors = data.reduce((acc, item) => acc + valueFor(item, "visitantes", year), 0);
  const spend = data.reduce((acc, item) => acc + valueFor(item, "gasto", year), 0);
  const opportunityValues = data.map((item) => valueFor(item, "oportunidad", year)).filter((value) => value > 0);
  const opportunity = opportunityValues.reduce((acc, value) => acc + value, 0) / (opportunityValues.length || 1);
  const municipalities = new Set(attractions.map((item) => item.municipio));
  const density = attractions.length / (municipalities.size || 1);

  document.getElementById("panel-subtitle").textContent = `${fmt(data.length)} municipios filtrados · ${fmt(attractions.length)} atractivos · ${selectedType() === "todos" ? "todos los tipos" : selectedType()}`;
  document.getElementById("kpi-visitors").textContent = fmt(visitors);
  document.getElementById("kpi-spend").textContent = fmt(spend);
  document.getElementById("kpi-opportunity").textContent = fmt(opportunity, 2);
  document.getElementById("kpi-density").textContent = fmt(density, 1);

  renderBars();
  renderRank("demand-ranking", rankBy("visitantes", year), (value) => fmt(value));
  renderRank("type-ranking", typeCounts(), (value) => `${fmt(value)} atr.`);
  renderRank("opportunity-ranking", rankBy("oportunidad", year), (value) => fmt(value, 2));

  const available = years();
  const index = available.indexOf(Number(year));
  document.getElementById("year-progress").style.width = `${available.length > 1 ? ((index + 1) / available.length) * 100 : 80}%`;
}

populateFilters();
["year-select", "type-select", "municipality-select"].forEach((id) => {
  document.getElementById(id).addEventListener("change", renderIndicators);
});
renderIndicators();
