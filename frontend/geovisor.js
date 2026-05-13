const DATA_SOURCE = "piloto_estatico";

const TOURISM_DATA = [
  {
    municipio: "Cali",
    lat: 3.4516,
    lng: -76.532,
    region: "Sur",
    atractivo: "Cultura urbana, salsa y eventos",
    visitantes: { 2025: 820000, 2026: 910000 },
    gasto: { 2025: 486, 2026: 548 },
    accesibilidad: { 2025: 0.91, 2026: 0.93 },
    oportunidad: { 2025: 0.86, 2026: 0.89 }
  },
  {
    municipio: "Buenaventura",
    lat: 3.8801,
    lng: -77.0312,
    region: "Pacifico",
    atractivo: "Avistamiento, playas y turismo comunitario",
    visitantes: { 2025: 260000, 2026: 310000 },
    gasto: { 2025: 132, 2026: 168 },
    accesibilidad: { 2025: 0.58, 2026: 0.62 },
    oportunidad: { 2025: 0.72, 2026: 0.77 }
  },
  {
    municipio: "Buga",
    lat: 3.9009,
    lng: -76.2978,
    region: "Centro",
    atractivo: "Turismo religioso y patrimonio",
    visitantes: { 2025: 390000, 2026: 430000 },
    gasto: { 2025: 210, 2026: 236 },
    accesibilidad: { 2025: 0.84, 2026: 0.86 },
    oportunidad: { 2025: 0.81, 2026: 0.83 }
  },
  {
    municipio: "Calima El Darien",
    lat: 3.931,
    lng: -76.484,
    region: "Centro",
    atractivo: "Embalse, deporte nautico y naturaleza",
    visitantes: { 2025: 180000, 2026: 225000 },
    gasto: { 2025: 104, 2026: 135 },
    accesibilidad: { 2025: 0.71, 2026: 0.74 },
    oportunidad: { 2025: 0.68, 2026: 0.73 }
  },
  {
    municipio: "Roldanillo",
    lat: 4.4126,
    lng: -76.1546,
    region: "Norte",
    atractivo: "Parapente, museo y paisaje cultural",
    visitantes: { 2025: 98000, 2026: 128000 },
    gasto: { 2025: 62, 2026: 82 },
    accesibilidad: { 2025: 0.64, 2026: 0.67 },
    oportunidad: { 2025: 0.59, 2026: 0.65 }
  },
  {
    municipio: "Sevilla",
    lat: 4.2643,
    lng: -75.9311,
    region: "Norte",
    atractivo: "Cafe, miradores y paisaje de cordillera",
    visitantes: { 2025: 72000, 2026: 96000 },
    gasto: { 2025: 48, 2026: 66 },
    accesibilidad: { 2025: 0.52, 2026: 0.57 },
    oportunidad: { 2025: 0.55, 2026: 0.61 }
  },
  {
    municipio: "Palmira",
    lat: 3.5394,
    lng: -76.3036,
    region: "Sur",
    atractivo: "Agroturismo, eventos y conectividad aeroportuaria",
    visitantes: { 2025: 230000, 2026: 265000 },
    gasto: { 2025: 118, 2026: 142 },
    accesibilidad: { 2025: 0.88, 2026: 0.9 },
    oportunidad: { 2025: 0.74, 2026: 0.78 }
  },
  {
    municipio: "Jamundi",
    lat: 3.2607,
    lng: -76.54,
    region: "Sur",
    atractivo: "Naturaleza, rios y borde metropolitano",
    visitantes: { 2025: 120000, 2026: 158000 },
    gasto: { 2025: 70, 2026: 92 },
    accesibilidad: { 2025: 0.78, 2026: 0.81 },
    oportunidad: { 2025: 0.63, 2026: 0.69 }
  }
];

const ACTIVE_TOURISM_DATA = (
  typeof window !== "undefined"
  && Array.isArray(window.GEOTURISMO_DATA)
  && window.GEOTURISMO_DATA.length
) ? window.GEOTURISMO_DATA : TOURISM_DATA;

const ACTIVE_ATTRACTIONS = (
  typeof window !== "undefined"
  && Array.isArray(window.GEOTURISMO_ATTRACTIONS)
  && window.GEOTURISMO_ATTRACTIONS.length
) ? window.GEOTURISMO_ATTRACTIONS : [];

const ACTIVE_TYPE_SUMMARY = (
  typeof window !== "undefined"
  && Array.isArray(window.GEOTURISMO_TYPE_SUMMARY)
) ? window.GEOTURISMO_TYPE_SUMMARY : [];

const ACTIVE_MUNICIPALITIES = (
  typeof window !== "undefined"
  && window.GEOTURISMO_MUNICIPALITIES
  && Array.isArray(window.GEOTURISMO_MUNICIPALITIES.features)
) ? window.GEOTURISMO_MUNICIPALITIES : { type: "FeatureCollection", features: [] };

const STATIC_TYPE_FALLBACK = [
  "Religioso",
  "Naturaleza",
  "Cultural",
  "Aventura",
  "Gastronomico",
  "Comunitario",
  "Patrimonial"
];

const ROUTES = [
  {
    name: "Corredor cultural y patrimonial",
    color: "#84cc16",
    stops: ["Cali", "Palmira", "Buga"]
  },
  {
    name: "Ruta naturaleza y agua",
    color: "#34d399",
    stops: ["Cali", "Calima El Darien", "Buenaventura"]
  },
  {
    name: "Norte aventura y cafe",
    color: "#65a30d",
    stops: ["Buga", "Roldanillo", "Sevilla"]
  }
];

const VARIABLE_META = {
  oportunidad: {
    label: "Indice de oportunidad",
    shortLabel: "indice 2026",
    totalLabel: "suma indice",
    suffix: "",
    decimals: 2
  },
  atractivos: {
    label: "Atractivos turisticos",
    shortLabel: "atractivos",
    totalLabel: "atractivos",
    suffix: "",
    decimals: 0
  },
  diversidad: {
    label: "Diversidad de tipos",
    shortLabel: "tipos de turismo",
    totalLabel: "tipos acumulados",
    suffix: "",
    decimals: 0
  },
  visitantes: {
    label: "Visitantes",
    shortLabel: "visitantes 2026",
    totalLabel: "visitantes 2026",
    suffix: "",
    decimals: 0
  },
  gasto: {
    label: "Gasto estimado",
    shortLabel: "gasto 2026",
    totalLabel: "gasto mm COP",
    suffix: " mm COP",
    decimals: 0
  },
  accesibilidad: {
    label: "Accesibilidad",
    shortLabel: "accesibilidad 2026",
    totalLabel: "suma accesibilidad",
    suffix: "",
    decimals: 2
  }
};

const COLOR_STOPS = [
  { label: "Muy alto", color: "#34d399" },
  { label: "Alto", color: "#84cc16" },
  { label: "Medio", color: "#d9a441" },
  { label: "Bajo", color: "#e76f51" }
];

const TYPE_COLORS = [
  "#34d399",
  "#84cc16",
  "#22c55e",
  "#65a30d",
  "#d9a441",
  "#10b981",
  "#a7f3d0",
  "#e76f51"
];

const map = L.map("map", {
  zoomControl: true,
  preferCanvas: true
}).setView([3.78, -76.43], 8);

L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
  attribution: "&copy; OpenStreetMap &copy; CARTO",
  subdomains: "abcd",
  maxZoom: 19
}).addTo(map);

let activeLayers = [];
let activeMode = "burbujas";

const fmt = (value, decimals = 0) => Number(value).toLocaleString("es-CO", {
  maximumFractionDigits: decimals,
  minimumFractionDigits: decimals
});

function normalizeKey(value) {
  const key = String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .trim();
  const aliases = {
    "SANTIAGO DE CALI": "CALI",
    "GUADALAJARA DE BUGA": "BUGA",
    "GUADALAJARA BUGA": "BUGA",
    "CALIMA": "CALIMA EL DARIEN",
    "EL DARIEN": "CALIMA EL DARIEN",
    "CALIMA DARIEN": "CALIMA EL DARIEN"
  };
  return aliases[key] || key;
}

function featureMunicipalityName(feature) {
  const props = feature.properties || {};
  const candidates = [
    props.municipio,
    props.MPIO_CNMBR,
    props.mpio_cnmbr,
    props.nombre,
    props.NOMBRE,
    props.NOM_MPIO,
    props.nombre_mun
  ].filter(Boolean);
  const usable = candidates.find((value) => normalizeKey(value) !== "MUNICIPIO");
  return usable || candidates[0] || "Municipio";
}

function featureMunicipalityKey(feature) {
  return normalizeKey(featureMunicipalityName(feature));
}

function currentFilters() {
  return {
    year: document.getElementById("year-select").value,
    variable: document.getElementById("variable-select").value,
    type: document.getElementById("type-select").value,
    includeCali: document.getElementById("include-cali").checked,
    mode: activeMode
  };
}

function filteredData(filters) {
  return ACTIVE_TOURISM_DATA.filter((item) => {
    const includeByCity = filters.includeCali || normalizeKey(item.municipio) !== "CALI";
    const itemTypes = [
      item.tipo_predominante,
      ...(Array.isArray(item.tipos_turismo) ? item.tipos_turismo : [])
    ].map(normalizeKey);
    const selectedType = normalizeKey(filters.type);
    const includeByType = filters.type === "todos"
      || itemTypes.includes(selectedType);
    return includeByCity && includeByType;
  });
}

function filteredAttractions(filters) {
  return ACTIVE_ATTRACTIONS.filter((item) => {
    const includeByCity = filters.includeCali || normalizeKey(item.municipio) !== "CALI";
    const itemTypes = [item.tipo_turismo, item.tipo_secundario].map(normalizeKey);
    const selectedType = normalizeKey(filters.type);
    const includeByType = filters.type === "todos"
      || itemTypes.includes(selectedType);
    return includeByCity && includeByType;
  });
}

function getValue(item, filters) {
  if (filters.mode === "cambio") {
    const years = availableYears();
    const currentYear = Number(filters.year);
    const currentIndex = years.indexOf(currentYear);
    const previousYear = currentIndex > 0 ? years[currentIndex - 1] : years[0];
    const previous = (item[filters.variable] || {})[previousYear] || 0;
    const current = (item[filters.variable] || {})[currentYear] || 0;
    if (filters.variable === "oportunidad" || filters.variable === "accesibilidad") {
      return current - previous;
    }
    return previous ? ((current - previous) / previous) * 100 : 0;
  }
  return (item[filters.variable] || {})[filters.year] || 0;
}

function availableYears() {
  const years = new Set();
  ACTIVE_TOURISM_DATA.forEach((item) => {
    Object.keys(item.visitantes || {}).forEach((year) => years.add(Number(year)));
  });
  return [...years].filter(Boolean).sort((a, b) => a - b);
}

function populateYearSelect() {
  const years = availableYears();
  const select = document.getElementById("year-select");
  if (!years.length || !select) return;
  const latest = years[years.length - 1];
  select.innerHTML = years.map((year) => (
    `<option value="${year}" ${year === latest ? "selected" : ""}>${year}</option>`
  )).join("");
}

function availableTypes() {
  const types = new Set();
  ACTIVE_TYPE_SUMMARY.forEach((item) => {
    if (item.tipo_turismo) types.add(item.tipo_turismo);
  });
  ACTIVE_ATTRACTIONS.forEach((item) => {
    if (item.tipo_turismo) types.add(item.tipo_turismo);
    if (item.tipo_secundario) types.add(item.tipo_secundario);
  });
  ACTIVE_TOURISM_DATA.forEach((item) => {
    if (item.tipo_predominante) types.add(item.tipo_predominante);
    if (Array.isArray(item.tipos_turismo)) item.tipos_turismo.forEach((type) => types.add(type));
  });
  return [...types].filter(Boolean).sort((a, b) => a.localeCompare(b, "es"));
}

function populateTypeSelect() {
  const select = document.getElementById("type-select");
  if (!select) return;
  const types = availableTypes();
  const options = types.length ? types : STATIC_TYPE_FALLBACK;
  select.innerHTML = [
    '<option value="todos">Todos los tipos</option>',
    ...options.map((type) => `<option value="${type}">${type}</option>`)
  ].join("");
}

function colorForType(type) {
  const types = availableTypes();
  const index = Math.max(0, types.indexOf(type));
  return TYPE_COLORS[index % TYPE_COLORS.length];
}

function clearLayers() {
  activeLayers.forEach((layer) => map.removeLayer(layer));
  activeLayers = [];
}

function colorFor(value, variable, mode) {
  if (mode === "cambio") {
    if (variable === "oportunidad" || variable === "accesibilidad") {
      if (value >= 0.12) return "#34d399";
      if (value >= 0.06) return "#84cc16";
      if (value >= 0.02) return "#d9a441";
      return "#e76f51";
    }
    if (value >= 18) return "#34d399";
    if (value >= 10) return "#84cc16";
    if (value >= 4) return "#d9a441";
    return "#e76f51";
  }
  if (variable === "oportunidad" || variable === "accesibilidad") {
    if (value >= 0.8) return "#34d399";
    if (value >= 0.68) return "#84cc16";
    if (value >= 0.58) return "#d9a441";
    return "#e76f51";
  }
  if (variable === "visitantes") {
    if (value >= 500000) return "#34d399";
    if (value >= 220000) return "#84cc16";
    if (value >= 100000) return "#d9a441";
    return "#e76f51";
  }
  if (variable === "atractivos") {
    if (value >= 12) return "#34d399";
    if (value >= 7) return "#84cc16";
    if (value >= 3) return "#d9a441";
    return "#e76f51";
  }
  if (variable === "diversidad") {
    if (value >= 5) return "#34d399";
    if (value >= 3) return "#84cc16";
    if (value >= 2) return "#d9a441";
    return "#e76f51";
  }
  if (value >= 300) return "#34d399";
  if (value >= 130) return "#84cc16";
  if (value >= 70) return "#d9a441";
  return "#e76f51";
}

function radiusFor(value, variable, mode) {
  const absolute = Math.abs(value);
  if (mode === "cambio") return Math.max(10, Math.min(40, 12 + absolute * 0.9));
  if (variable === "visitantes") return Math.max(9, Math.min(46, Math.sqrt(value) / 22));
  if (variable === "gasto") return Math.max(9, Math.min(42, value / 9));
  if (variable === "atractivos") return Math.max(11, Math.min(42, 9 + value * 2.2));
  if (variable === "diversidad") return Math.max(11, Math.min(38, 10 + value * 5));
  return 11 + value * 28;
}

function formatValue(value, filters) {
  const meta = VARIABLE_META[filters.variable];
  if (filters.mode === "cambio") {
    const suffix = filters.variable === "oportunidad" || filters.variable === "accesibilidad" ? " pts" : "%";
    const decimals = suffix === "%" ? 1 : 2;
    return `${fmt(value, decimals)}${suffix}`;
  }
  return `${fmt(value, meta.decimals)}${meta.suffix}`;
}

function popupHtml(item, filters) {
  const meta = VARIABLE_META[filters.variable];
  const value = getValue(item, filters);
  return `<div>
    <div class="popup-title">${item.municipio}</div>
    <div class="popup-row"><span>Region</span><strong>${item.region}</strong></div>
    <div class="popup-row"><span>Tipo principal</span><strong>${item.tipo_predominante || "Mixto"}</strong></div>
    <div class="popup-row"><span>${filters.mode === "cambio" ? "Cambio 2025-26" : meta.label}</span><strong>${formatValue(value, filters)}</strong></div>
    <div class="popup-row"><span>Visitantes</span><strong>${fmt((item.visitantes || {})[filters.year] || 0)}</strong></div>
    <div class="popup-row"><span>Atractivo</span><strong>${item.atractivo}</strong></div>
  </div>`;
}

function attractionPopupHtml(item) {
  return `<div>
    <div class="popup-title">${item.nombre}</div>
    <div class="popup-row"><span>Municipio</span><strong>${item.municipio}</strong></div>
    <div class="popup-row"><span>Tipo</span><strong>${item.tipo_turismo || "Sin clasificar"}</strong></div>
    <div class="popup-row"><span>Tipo secundario</span><strong>${item.tipo_secundario || "-"}</strong></div>
    <div class="popup-row"><span>Actividades</span><strong>${item.actividades || "-"}</strong></div>
    <div class="popup-row"><span>Altitud</span><strong>${item.altitud || "-"}</strong></div>
    <div class="popup-row"><span>Temperatura</span><strong>${item.temperatura || "-"}</strong></div>
  </div>`;
}

function markerOptions(item, filters, fixedRadius = false) {
  const value = getValue(item, filters);
  return {
    radius: fixedRadius ? 18 : radiusFor(value, filters.variable, filters.mode),
    color: colorFor(value, filters.variable, filters.mode),
    weight: fixedRadius ? 2 : 1.8,
    opacity: 0.95,
    fillColor: colorFor(value, filters.variable, filters.mode),
    fillOpacity: fixedRadius ? 0.36 : 0.48
  };
}

function renderBubbleLayer(data, filters) {
  data.forEach((item) => {
    const marker = L.circleMarker([item.lat, item.lng], markerOptions(item, filters))
      .bindPopup(popupHtml(item, filters));
    marker.addTo(map);
    activeLayers.push(marker);
  });
}

function renderAttractionsLayer(attractions) {
  attractions.forEach((item) => {
    const color = colorForType(item.tipo_turismo);
    const marker = L.circleMarker([item.lat, item.lng], {
      radius: 7,
      color,
      weight: 2,
      opacity: 0.95,
      fillColor: color,
      fillOpacity: 0.72
    }).bindPopup(attractionPopupHtml(item));
    marker.addTo(map);
    activeLayers.push(marker);
  });
}

function renderChoroplethLikeLayer(data, filters) {
  if (ACTIVE_MUNICIPALITIES.features.length) {
    renderMunicipalityPolygons(data, filters);
    return;
  }
  data.forEach((item) => {
    const marker = L.circleMarker([item.lat, item.lng], markerOptions(item, filters, true))
      .bindPopup(popupHtml(item, filters));
    marker.addTo(map);
    activeLayers.push(marker);
  });
}

function dataByMunicipality(data) {
  return Object.fromEntries(data.map((item) => [normalizeKey(item.municipio), item]));
}

function attractionStatsByMunicipality(filters) {
  const stats = {};
  filteredAttractions(filters).forEach((item) => {
    const key = normalizeKey(item.municipio);
    if (!stats[key]) stats[key] = { atractivos: 0, tipos: new Set() };
    stats[key].atractivos += 1;
    if (item.tipo_turismo) stats[key].tipos.add(item.tipo_turismo);
    if (item.tipo_secundario) stats[key].tipos.add(item.tipo_secundario);
  });
  return stats;
}

function polygonValue(feature, dataIndex, typeStats, filters) {
  const key = featureMunicipalityKey(feature);
  if (filters.type !== "todos") {
    const stats = typeStats[key];
    if (!stats) return 0;
    if (filters.variable === "diversidad") return stats.tipos.size;
    return stats.atractivos;
  }
  const item = dataIndex[key];
  if (!item) return 0;
  return getValue(item, filters);
}

function municipalityFeaturesForYear(filters) {
  const features = ACTIVE_MUNICIPALITIES.features || [];
  const yearFeatures = features.filter((feature) => String(feature.properties.anio || "") === String(filters.year));
  return yearFeatures.length ? yearFeatures : features;
}

function polygonValues(features, dataIndex, typeStats, filters) {
  return features.map((feature) => polygonValue(feature, dataIndex, typeStats, filters));
}

function choroplethBreaks(values) {
  const positives = values.filter((value) => Number(value) > 0);
  const max = positives.length ? Math.max(...positives) : 0;
  if (!max) return { max: 0, breaks: [0, 0, 0] };
  return {
    max,
    breaks: [max * 0.25, max * 0.5, max * 0.75]
  };
}

function choroplethColor(value, scale) {
  if (!value || !scale.max) return "#102419";
  if (value <= scale.breaks[0]) return "#e76f51";
  if (value <= scale.breaks[1]) return "#d9a441";
  if (value <= scale.breaks[2]) return "#84cc16";
  return "#34d399";
}

function polygonPopupHtml(feature, value, filters) {
  const name = featureMunicipalityName(feature);
  const label = filters.type !== "todos" ? `Atractivos ${filters.type}` : VARIABLE_META[filters.variable].label;
  const renderedValue = filters.type !== "todos" ? fmt(value) : formatValue(value, filters);
  return `<div>
    <div class="popup-title">${name}</div>
    <div class="popup-row"><span>${label}</span><strong>${renderedValue}</strong></div>
    <div class="popup-row"><span>Filtro tipo</span><strong>${filters.type === "todos" ? "Todos" : filters.type}</strong></div>
  </div>`;
}

function renderMunicipalityPolygons(data, filters) {
  const dataIndex = dataByMunicipality(data);
  const typeStats = attractionStatsByMunicipality(filters);
  const features = municipalityFeaturesForYear(filters);
  const scale = choroplethBreaks(polygonValues(features, dataIndex, typeStats, filters));
  const layer = L.geoJSON({ type: "FeatureCollection", features }, {
    style: (feature) => {
      const value = polygonValue(feature, dataIndex, typeStats, filters);
      return {
        color: value > 0 ? "#b7f04b" : "#245136",
        weight: value > 0 ? 1.4 : 0.8,
        fillColor: choroplethColor(value, scale),
        fillOpacity: value > 0 ? 0.62 : 0.1
      };
    },
    onEachFeature: (feature, layerItem) => {
      const value = polygonValue(feature, dataIndex, typeStats, filters);
      layerItem.bindPopup(polygonPopupHtml(feature, value, filters));
    }
  });
  layer.addTo(map);
  activeLayers.push(layer);
}

function renderHeatLayer(data, filters) {
  data.forEach((item) => {
    const value = getValue(item, filters);
    const color = colorFor(value, filters.variable, filters.mode);
    const heat = L.circle([item.lat, item.lng], {
      radius: radiusFor(value, filters.variable, filters.mode) * 2800,
      color,
      weight: 0,
      fillColor: color,
      fillOpacity: 0.18
    }).bindPopup(popupHtml(item, filters));
    heat.addTo(map);
    activeLayers.push(heat);
  });
  renderBubbleLayer(data, filters);
}

function renderRoutesLayer(data, filters) {
  const byName = Object.fromEntries(data.map((item) => [item.municipio, item]));
  ROUTES.forEach((route) => {
    const coords = route.stops
      .map((name) => byName[name])
      .filter(Boolean)
      .map((item) => [item.lat, item.lng]);
    if (coords.length < 2) return;
    const line = L.polyline(coords, {
      color: route.color,
      weight: 4,
      opacity: 0.88
    }).bindPopup(`<strong>${route.name}</strong><br>${route.stops.join(" - ")}`);
    line.addTo(map);
    activeLayers.push(line);
  });
  renderBubbleLayer(data, filters);
}

function updateLegend(filters) {
  if (filters.mode === "atractivos") {
    const types = availableTypes().filter((type) => filters.type === "todos" || filters.type === type);
    document.getElementById("legend-list").innerHTML = types.slice(0, 8).map((type) => (
      `<div class="legend-row"><span class="legend-dot" style="background:${colorForType(type)}"></span><span>${type}</span></div>`
    )).join("") || '<div class="legend-row"><span>Sin tipos disponibles</span></div>';
    return;
  }
  if (filters.mode === "coropletico" || filters.mode === "cambio" || filters.type !== "todos") {
    const dataIndex = dataByMunicipality(filteredData(filters));
    const typeStats = attractionStatsByMunicipality(filters);
    const features = municipalityFeaturesForYear(filters);
    const scale = choroplethBreaks(polygonValues(features, dataIndex, typeStats, filters));
    if (!scale.max) {
      document.getElementById("legend-list").innerHTML = '<div class="legend-row"><span>Sin datos para el filtro</span></div>';
      return;
    }
    const rows = [
      { label: `0 - ${fmt(scale.breaks[0], 1)}`, color: "#e76f51" },
      { label: `${fmt(scale.breaks[0], 1)} - ${fmt(scale.breaks[1], 1)}`, color: "#d9a441" },
      { label: `${fmt(scale.breaks[1], 1)} - ${fmt(scale.breaks[2], 1)}`, color: "#84cc16" },
      { label: `${fmt(scale.breaks[2], 1)} - ${fmt(scale.max, 1)}`, color: "#34d399" }
    ];
    document.getElementById("legend-list").innerHTML = rows.map((row) => (
      `<div class="legend-row"><span class="legend-dot" style="background:${row.color}"></span><span>${row.label}</span></div>`
    )).join("");
    return;
  }
  document.getElementById("legend-list").innerHTML = COLOR_STOPS.map((stop) => (
    `<div class="legend-row"><span class="legend-dot" style="background:${stop.color}"></span><span>${stop.label}</span></div>`
  )).join("");
}

function updateModeButtons() {
  document.querySelectorAll(".map-mode-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === activeMode);
  });
}

function updateProgress(filters) {
  const yearProgress = filters.year === "2026" ? "86%" : "62%";
  document.getElementById("year-progress").style.width = yearProgress;
}

function updateSummary(data, attractions, filters) {
  if (filters.mode === "atractivos" || filters.type !== "todos") {
    const municipalities = new Set(attractions.map((item) => item.municipio));
    const types = new Set(attractions.map((item) => item.tipo_turismo).filter(Boolean));
    const sortedTypes = [...types].map((type) => ({
      type,
      count: attractions.filter((item) => item.tipo_turismo === type).length
    })).sort((a, b) => b.count - a.count);

    document.getElementById("summary-total").textContent = fmt(attractions.length);
    document.getElementById("summary-total-label").textContent = filters.type === "todos" ? "atractivos" : `atractivos ${filters.type}`;
    document.getElementById("summary-average").textContent = fmt(types.size);
    document.getElementById("summary-average-label").textContent = "tipos de turismo";
    document.getElementById("summary-count").textContent = fmt(municipalities.size);
    if (filters.type === "todos") {
      document.getElementById("summary-leader").textContent = sortedTypes[0] ? `Tipo lider: ${sortedTypes[0].type}` : "Tipo lider: -";
      document.getElementById("ranking-list").innerHTML = sortedTypes.slice(0, 5).map((item) => (
        `<li><strong>${item.type}</strong><span>${fmt(item.count)} atractivos</span></li>`
      )).join("");
    } else {
      const byMunicipality = [...municipalities].map((municipio) => ({
        municipio,
        count: attractions.filter((item) => item.municipio === municipio).length
      })).sort((a, b) => b.count - a.count);
      document.getElementById("summary-leader").textContent = byMunicipality[0] ? `Municipio lider: ${byMunicipality[0].municipio}` : "Municipio lider: -";
      document.getElementById("ranking-list").innerHTML = byMunicipality.slice(0, 5).map((item) => (
        `<li><strong>${item.municipio}</strong><span>${fmt(item.count)} atractivos</span></li>`
      )).join("");
    }
    return;
  }

  const values = data.map((item) => getValue(item, filters));
  const sorted = [...data].sort((a, b) => getValue(b, filters) - getValue(a, filters));
  const meta = VARIABLE_META[filters.variable];
  const total = values.reduce((acc, value) => acc + value, 0);
  const average = total / (values.length || 1);
  const totalDecimals = filters.variable === "oportunidad" || filters.variable === "accesibilidad" ? 2 : 0;

  document.getElementById("summary-total").textContent = fmt(total, activeMode === "cambio" ? 1 : totalDecimals);
  document.getElementById("summary-total-label").textContent = activeMode === "cambio" ? "cambio acumulado" : meta.totalLabel;
  document.getElementById("summary-average").textContent = fmt(average, activeMode === "cambio" ? 2 : meta.decimals);
  document.getElementById("summary-average-label").textContent = activeMode === "cambio" ? "cambio promedio" : "promedio";
  document.getElementById("summary-count").textContent = fmt(data.length);
  document.getElementById("summary-leader").textContent = sorted[0] ? `Destino lider: ${sorted[0].municipio}` : "Destino lider: -";

  document.getElementById("ranking-list").innerHTML = sorted.slice(0, 5).map((item) => {
    const value = getValue(item, filters);
    return `<li><strong>${item.municipio}</strong><span>${formatValue(value, filters)}</span></li>`;
  }).join("");
}

function renderMap() {
  const filters = currentFilters();
  const data = filteredData(filters);
  const attractions = filteredAttractions(filters);
  clearLayers();

  if (filters.mode === "atractivos") renderAttractionsLayer(attractions);
  if (filters.mode === "calor") renderHeatLayer(data, filters);
  if (filters.mode === "rutas") renderRoutesLayer(data, filters);
  if (filters.mode === "burbujas") renderBubbleLayer(data, filters);
  if (filters.mode === "coropletico" || filters.mode === "cambio") renderChoroplethLikeLayer(data, filters);

  updateLegend(filters);
  updateSummary(data, attractions, filters);
  updateModeButtons();
  updateProgress(filters);

  const boundsData = filters.mode === "atractivos" ? attractions : data;
  if ((filters.mode === "coropletico" || filters.mode === "cambio") && ACTIVE_MUNICIPALITIES.features.length) {
    const polygonLayer = activeLayers[activeLayers.length - 1];
    if (polygonLayer && polygonLayer.getBounds) {
      map.fitBounds(polygonLayer.getBounds().pad(0.08));
    }
  } else if (boundsData.length) {
    const bounds = L.latLngBounds(boundsData.map((item) => [item.lat, item.lng]));
    map.fitBounds(bounds.pad(0.18));
  }
}

document.getElementById("year-select").addEventListener("change", renderMap);
document.getElementById("variable-select").addEventListener("change", renderMap);
document.getElementById("type-select").addEventListener("change", renderMap);
document.getElementById("include-cali").addEventListener("change", renderMap);
document.querySelectorAll(".map-mode-btn").forEach((button) => {
  button.addEventListener("click", () => {
    activeMode = button.dataset.mode;
    renderMap();
  });
});

populateYearSelect();
populateTypeSelect();
renderMap();
