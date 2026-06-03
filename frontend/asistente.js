/**
 * asistente.js — Panel de chat del Asistente IA
 * Observatorio GeoTurismo · Valle del Cauca
 *
 * Conecta el chat con el servidor FastAPI en localhost:8081.
 * Funciona en modo local (sin Gemini) y modo completo (con Gemini).
 * Implementa window.applyGeoTurismoChatAction() para que el agente
 * pueda controlar el dashboard (filtros, secciones, geovisor).
 */

(() => {
  // ── Configuración ──────────────────────────────────────────────────────────
  const API_BASE   = window.location.protocol.startsWith("http")
                     ? window.location.origin + "/api/geoturismo"
                     : "http://localhost:8081";
  const SESSION_ID = "obs_" + Math.random().toString(36).slice(2, 10);

  const SUGERENCIAS = [
    "¿Qué municipios cubre el observatorio?",
    "¿Cuántos visitantes tuvo Cali en 2024?",
    "Dame el top 5 de municipios más visitados en 2024",
    "¿Qué atractivos tiene Buga?",
    "Resumen del turismo en el Valle en 2023",
    "¿Qué municipios tienen ecoturismo?",
    "Muéstrame el mapa de visitantes en 2024",
    "Evolución histórica de Palmira",
  ];

  // ── Estado ─────────────────────────────────────────────────────────────────
  let panelAbierto = false;
  let esperandoRespuesta = false;
  let modoFallback = false;
  let servidorDisponible = null; // null = no verificado

  // ── Inyectar HTML del panel ────────────────────────────────────────────────
  const panelHTML = `
<div id="chat-drawer" aria-label="Asistente IA" role="complementary" aria-hidden="true">
  <div id="chat-header">
    <div id="chat-header-left">
      <span id="chat-icon">⊙</span>
      <div>
        <span id="chat-title">Asistente IA</span>
        <span id="chat-subtitle">GeoTurismo · Valle del Cauca</span>
      </div>
    </div>
    <div id="chat-header-right">
      <span id="chat-status-badge" title="Estado del servidor">●</span>
      <button id="chat-close" aria-label="Cerrar asistente" title="Cerrar">✕</button>
    </div>
  </div>

  <div id="chat-status-bar" class="hidden">
    <span id="chat-status-text"></span>
  </div>

  <div id="chat-messages" role="log" aria-live="polite"></div>

  <div id="chat-suggestions-wrap">
    <p id="chat-suggestions-label">Preguntas sugeridas</p>
    <div id="chat-suggestions"></div>
  </div>

  <form id="chat-form" autocomplete="off">
    <textarea
      id="chat-input"
      placeholder="Pregunta sobre municipios, visitantes, atractivos…"
      rows="1"
      maxlength="400"
      aria-label="Mensaje para el asistente"
    ></textarea>
    <button type="submit" id="chat-send" aria-label="Enviar" title="Enviar">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M14.5 8L2 13.5L4.5 8L2 2.5L14.5 8Z" fill="currentColor"/>
      </svg>
    </button>
  </form>
</div>
<div id="chat-overlay"></div>
`;

  const panelCSS = `
/* ── Chat Drawer ─────────────────────────────────────────────────── */
#chat-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  z-index: 199;
  backdrop-filter: blur(2px);
}
#chat-overlay.active { display: block; }

#chat-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  max-width: 96vw;
  height: 100vh;
  background: var(--panel, #0b1a12);
  border-left: 1px solid var(--line, #193324);
  display: flex;
  flex-direction: column;
  z-index: 200;
  transform: translateX(100%);
  transition: transform .28s cubic-bezier(.4,0,.2,1);
  font-family: var(--font, "Segoe UI", Arial, sans-serif);
}
#chat-drawer::before {
  content: "";
  height: 3px;
  background: linear-gradient(90deg, var(--accent,#34d399), var(--accent-2,#84cc16), var(--blue,#38bdf8));
  flex-shrink: 0;
}
#chat-drawer.open {
  transform: translateX(0);
  box-shadow: -8px 0 40px rgba(0,0,0,.5);
}

/* Header */
#chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--line, #193324);
  flex-shrink: 0;
}
#chat-header-left { display: flex; align-items: center; gap: 10px; }
#chat-icon {
  font-size: 20px;
  color: var(--accent, #34d399);
  line-height: 1;
}
#chat-title {
  display: block;
  font-size: 13px;
  font-weight: 800;
  color: var(--text, #e8f5ec);
  letter-spacing: .3px;
}
#chat-subtitle {
  display: block;
  font-size: 10px;
  color: var(--text-3, #5f806a);
  text-transform: uppercase;
  letter-spacing: .7px;
  margin-top: 2px;
}
#chat-header-right { display: flex; align-items: center; gap: 8px; }
#chat-status-badge {
  font-size: 12px;
  color: var(--text-3, #5f806a);
  transition: color .3s;
}
#chat-status-badge.online  { color: var(--accent, #34d399); }
#chat-status-badge.offline { color: var(--danger, #e76f51); }
#chat-status-badge.fallback { color: var(--warn, #d9a441); }
#chat-close {
  background: transparent;
  border: none;
  color: var(--text-3, #5f806a);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  line-height: 1;
  transition: color .15s, background .15s;
}
#chat-close:hover { color: var(--text, #e8f5ec); background: var(--panel-2, #102419); }

/* Status bar */
#chat-status-bar {
  padding: 6px 14px;
  font-size: 11px;
  border-bottom: 1px solid var(--line, #193324);
  flex-shrink: 0;
}
#chat-status-bar.hidden { display: none; }
#chat-status-bar.fallback-mode {
  background: rgba(217,164,65,.12);
  color: var(--warn, #d9a441);
  border-bottom-color: rgba(217,164,65,.25);
}
#chat-status-bar.error-mode {
  background: rgba(231,111,81,.1);
  color: var(--danger, #e76f51);
  border-bottom-color: rgba(231,111,81,.2);
}

/* Messages */
#chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scroll-behavior: smooth;
}
#chat-messages::-webkit-scrollbar { width: 4px; }
#chat-messages::-webkit-scrollbar-track { background: transparent; }
#chat-messages::-webkit-scrollbar-thumb {
  background: var(--line-2, #245136);
  border-radius: 2px;
}

.chat-msg {
  display: flex;
  flex-direction: column;
  max-width: 88%;
  animation: msgIn .2s ease;
}
@keyframes msgIn {
  from { opacity:0; transform: translateY(6px); }
  to   { opacity:1; transform: translateY(0); }
}
.chat-msg.user { align-self: flex-end; align-items: flex-end; }
.chat-msg.bot  { align-self: flex-start; align-items: flex-start; }

.chat-bubble {
  padding: 9px 13px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}
.chat-msg.user .chat-bubble {
  background: rgba(52,211,153,.18);
  border: 1px solid rgba(52,211,153,.35);
  color: var(--text, #e8f5ec);
  border-bottom-right-radius: 3px;
}
.chat-msg.bot .chat-bubble {
  background: var(--panel-2, #102419);
  border: 1px solid var(--line-2, #245136);
  color: var(--text, #e8f5ec);
  border-bottom-left-radius: 3px;
}
.chat-msg.bot .chat-bubble.action-bubble {
  border-color: rgba(52,211,153,.4);
  color: var(--accent, #34d399);
  font-size: 12px;
}
.chat-msg.bot .chat-bubble.fallback-bubble {
  border-color: rgba(217,164,65,.3);
}
.chat-time {
  font-size: 10px;
  color: var(--text-3, #5f806a);
  margin-top: 3px;
  padding: 0 3px;
}

/* Typing dots */
.chat-typing {
  display: flex;
  gap: 5px;
  padding: 11px 14px;
  background: var(--panel-2, #102419);
  border: 1px solid var(--line-2, #245136);
  border-radius: 10px;
  border-bottom-left-radius: 3px;
  width: fit-content;
  align-self: flex-start;
}
.chat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent, #34d399);
  animation: dotBounce 1.2s infinite ease-in-out;
}
.chat-dot:nth-child(2) { animation-delay: .18s; }
.chat-dot:nth-child(3) { animation-delay: .36s; }
@keyframes dotBounce {
  0%,80%,100% { transform: translateY(0); opacity:.4; }
  40% { transform: translateY(-6px); opacity:1; }
}

/* Suggestions */
#chat-suggestions-wrap {
  padding: 10px 12px 6px;
  border-top: 1px solid var(--line, #193324);
  flex-shrink: 0;
}
#chat-suggestions-wrap.hidden { display: none; }
#chat-suggestions-label {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: .8px;
  color: var(--text-3, #5f806a);
  margin: 0 0 6px;
}
#chat-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  max-height: 96px;
  overflow-y: auto;
}
#chat-suggestions::-webkit-scrollbar { display: none; }
.chat-chip {
  padding: 4px 9px;
  background: transparent;
  border: 1px solid var(--line-2, #245136);
  border-radius: 20px;
  color: var(--text-2, #a9c7b4);
  font-size: 11px;
  cursor: pointer;
  transition: border-color .15s, color .15s, background .15s;
  white-space: nowrap;
  font-family: var(--font, "Segoe UI", Arial, sans-serif);
}
.chat-chip:hover {
  border-color: var(--accent, #34d399);
  color: var(--accent, #34d399);
  background: rgba(52,211,153,.08);
}

/* Form / Input */
#chat-form {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px 14px;
  border-top: 1px solid var(--line, #193324);
  flex-shrink: 0;
}
#chat-input {
  flex: 1;
  background: var(--panel-2, #102419);
  border: 1px solid var(--line-2, #245136);
  border-radius: 8px;
  color: var(--text, #e8f5ec);
  font-size: 13px;
  padding: 9px 11px;
  resize: none;
  line-height: 1.4;
  max-height: 120px;
  overflow-y: auto;
  transition: border-color .15s;
  font-family: var(--font, "Segoe UI", Arial, sans-serif);
}
#chat-input::placeholder { color: var(--text-3, #5f806a); }
#chat-input:focus {
  outline: none;
  border-color: var(--accent, #34d399);
}
#chat-send {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  background: var(--accent, #34d399);
  border: none;
  border-radius: 8px;
  color: #06100b;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background .15s, transform .1s;
}
#chat-send:hover  { background: var(--accent-3, #22c55e); }
#chat-send:active { transform: scale(.94); }
#chat-send:disabled {
  background: var(--line-2, #245136);
  cursor: not-allowed;
  color: var(--text-3, #5f806a);
}

/* Artifacts (imágenes generadas) */
.chat-artifact-img {
  max-width: 100%;
  border-radius: 6px;
  border: 1px solid var(--line-2, #245136);
  margin-top: 6px;
}
`;

  // Inyectar estilos
  const styleEl = document.createElement("style");
  styleEl.textContent = panelCSS;
  document.head.appendChild(styleEl);

  // Inyectar HTML
  document.body.insertAdjacentHTML("beforeend", panelHTML);

  // ── Referencias DOM ────────────────────────────────────────────────────────
  const drawer        = document.getElementById("chat-drawer");
  const overlay       = document.getElementById("chat-overlay");
  const btnClose      = document.getElementById("chat-close");
  const messages      = document.getElementById("chat-messages");
  const form          = document.getElementById("chat-form");
  const input         = document.getElementById("chat-input");
  const btnSend       = document.getElementById("chat-send");
  const statusBadge   = document.getElementById("chat-status-badge");
  const statusBar     = document.getElementById("chat-status-bar");
  const statusText    = document.getElementById("chat-status-text");
  const suggestWrap   = document.getElementById("chat-suggestions-wrap");
  const suggestCont   = document.getElementById("chat-suggestions");

  // ── Abrir / cerrar panel ───────────────────────────────────────────────────
  function abrirPanel() {
    panelAbierto = true;
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
    overlay.classList.add("active");
    document.body.style.overflow = "hidden";
    input.focus();
    if (servidorDisponible === null) verificarServidor();
  }

  function cerrarPanel() {
    panelAbierto = false;
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    overlay.classList.remove("active");
    document.body.style.overflow = "";
  }

  // Interceptar el link #asistente en el sidebar
  document.querySelectorAll('a[href="#asistente"]').forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      abrirPanel();
      // Marcar como activo
      document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
      link.classList.add("active");
    });
  });

  btnClose.addEventListener("click", cerrarPanel);
  overlay.addEventListener("click", cerrarPanel);

  // ── Verificar servidor ─────────────────────────────────────────────────────
  async function verificarServidor() {
    try {
      const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
      const data = await res.json();
      servidorDisponible = data.status === "ok";
      setEstado("online");
    } catch {
      servidorDisponible = false;
      setEstado("offline");
    }
  }

  function setEstado(estado) {
    statusBadge.className = estado;
    statusBar.className   = "";

    if (estado === "online") {
      statusBar.classList.add("hidden");
    } else if (estado === "fallback") {
      modoFallback = true;
      statusBar.classList.add("fallback-mode");
      statusText.textContent = "⚡ Modo local activo · Gemini sin cuota · Datos y acciones disponibles";
    } else if (estado === "offline") {
      statusBar.classList.add("error-mode");
      statusText.textContent = "⚠ Servidor no disponible · Inicia uvicorn en localhost:8081";
    }
  }

  // ── Chips de sugerencias ───────────────────────────────────────────────────
  SUGERENCIAS.forEach(texto => {
    const btn = document.createElement("button");
    btn.className = "chat-chip";
    btn.type = "button";
    btn.textContent = texto;
    btn.addEventListener("click", () => {
      if (!esperandoRespuesta) enviarMensaje(texto);
    });
    suggestCont.appendChild(btn);
  });

  // ── Renderizar mensajes ────────────────────────────────────────────────────
  function renderMensaje(texto, rol, extra = {}) {
    const wrap   = document.createElement("div");
    wrap.className = `chat-msg ${rol}`;

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";

    if (extra.esAccion)   bubble.classList.add("action-bubble");
    if (extra.esFallback) bubble.classList.add("fallback-bubble");

    bubble.textContent = texto;

    const time = document.createElement("span");
    time.className = "chat-time";
    time.textContent = new Date().toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });

    wrap.appendChild(bubble);
    wrap.appendChild(time);

    // Imágenes de artifacts
    if (extra.artifacts && extra.artifacts.length) {
      extra.artifacts.forEach(fn => {
        const img = document.createElement("img");
        img.src = `${API_BASE}/artifacts/${fn}?session_id=${SESSION_ID}`;
        img.className = "chat-artifact-img";
        img.alt = fn;
        img.loading = "lazy";
        wrap.appendChild(img);
      });
    }

    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
    return wrap;
  }

  function mostrarTyping() {
    const wrap = document.createElement("div");
    wrap.className = "chat-typing";
    wrap.id = "chat-typing";
    [1,2,3].forEach(() => {
      const d = document.createElement("div");
      d.className = "chat-dot";
      wrap.appendChild(d);
    });
    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
  }

  function quitarTyping() {
    document.getElementById("chat-typing")?.remove();
  }

  // ── Enviar mensaje ─────────────────────────────────────────────────────────
  async function enviarMensaje(texto) {
    texto = texto.trim();
    if (!texto || esperandoRespuesta) return;

    // Ocultar sugerencias tras primer mensaje
    suggestWrap.classList.add("hidden");

    esperandoRespuesta = true;
    btnSend.disabled = true;
    input.value = "";
    input.style.height = "auto";

    renderMensaje(texto, "user");
    mostrarTyping();

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: SESSION_ID, message: texto }),
        signal: AbortSignal.timeout(25000),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      quitarTyping();

      const esFallback = data.reply?.includes("Cuota de Gemini") ||
                         data.reply?.includes("modo local") ||
                         data.reply?.includes("locales:");

      if (esFallback && !modoFallback) setEstado("fallback");

      renderMensaje(data.reply || "(sin respuesta)", "bot", {
        artifacts: data.artifacts || [],
        esFallback,
      });

      // Aplicar acciones de UI
      if (data.actions && data.actions.length) {
        data.actions.forEach(accion => {
          applyGeoTurismoChatAction(accion);
          const labelAccion = accionLabel(accion);
          if (labelAccion) renderMensaje(labelAccion, "bot", { esAccion: true });
        });
      }

      servidorDisponible = true;
      if (!modoFallback) setEstado("online");

    } catch (err) {
      quitarTyping();
      if (err.name === "TimeoutError") {
        renderMensaje("El servidor tardó demasiado. Verifica que uvicorn esté corriendo.", "bot");
      } else if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        servidorDisponible = false;
        setEstado("offline");
        renderMensaje(
          "No puedo conectar con el servidor. Asegúrate de que uvicorn esté corriendo en puerto 8081:\n\ncd chatbot\nuvicorn server:app --port 8081 --reload",
          "bot"
        );
      } else {
        renderMensaje(`Error: ${err.message}`, "bot");
      }
    } finally {
      esperandoRespuesta = false;
      btnSend.disabled = false;
      input.focus();
    }
  }

  // ── Descripción legible de una acción UI ──────────────────────────────────
  function accionLabel(accion) {
    if (!accion) return null;
    const secciones = {
      dashboard: "Panel de control",
      indicadores: "Indicadores",
      tendencias: "Tendencias",
      priorizacion: "Priorización",
      geovisor: "Geovisor",
      coropletico: "Mapa coroplético",
      atractivos: "Atractivos turísticos",
    };
    if (accion.type === "navigate") {
      const sec = secciones[accion.section] || accion.section;
      return `↗ Navegando a ${sec}${accion.anio ? ` · ${accion.anio}` : ""}`;
    }
    if (accion.type === "show_geovisor") {
      const vars = { visitantes: "Visitantes", indice_oportunidad_turistica: "Índice de oportunidad",
                     ocupacion_hotelera: "Ocupación hotelera", gasto_estimado: "Gasto estimado" };
      const varLabel = vars[accion.variable] || accion.variable || "Visitantes";
      const modeLabel = accion.mode === "coropletico" ? "Mapa coroplético" :
                        accion.mode === "calor"        ? "Mapa de calor" : "Burbujas";
      return `🗺 ${modeLabel} · ${varLabel}${accion.anio ? ` · ${accion.anio}` : ""}`;
    }
    return null;
  }

  // ── Aplicar acciones del agente al dashboard ───────────────────────────────
  window.applyGeoTurismoChatAction = function(accion) {
    if (!accion || !accion.type) return;

    if (accion.type === "navigate") {
      const sectionMap = {
        dashboard:    "#app",
        indicadores:  "#indicadores",
        tendencias:   "#tendencias",
        priorizacion: "#priorizacion",
        geovisor:     null,
        coropletico:  null,
        atractivos:   null,
      };
      // Actualizar año si viene
      if (accion.anio) {
        const sel = document.getElementById("year-select");
        if (sel) { sel.value = String(accion.anio); sel.dispatchEvent(new Event("change")); }
      }
      const target = sectionMap[accion.section];
      if (target) {
        const el = document.querySelector(target);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      } else if (accion.section === "geovisor") {
        window.open("geovisor.html", "_self");
      }
      // Marcar nav item
      document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
      const navLink = document.querySelector(`.nav-item[href="#${accion.section}"]`) ||
                      document.querySelector(`.nav-item[href="geovisor.html"]`);
      if (navLink) navLink.classList.add("active");
    }

    if (accion.type === "show_geovisor") {
      // Actualizar filtros del dashboard si están disponibles
      if (accion.anio) {
        const sel = document.getElementById("year-select");
        if (sel) { sel.value = String(accion.anio); sel.dispatchEvent(new Event("change")); }
      }
      // Mapear variable al select de métrica
      const varToMetric = {
        "visitantes":                   "visitantes",
        "indice_oportunidad_turistica":  "oportunidad",
        "indice_oportunidad":            "oportunidad",
        "ocupacion_hotelera":            "oportunidad",
        "gasto_estimado":                "gasto",
      };
      const metric = varToMetric[accion.variable];
      if (metric) {
        const sel = document.getElementById("metric-select");
        if (sel) { sel.value = metric; sel.dispatchEvent(new Event("change")); }
      }
      // Si el modo requiere geovisor completo, redirigir
      if (accion.mode === "burbujas" || accion.mode === "calor") {
        const params = new URLSearchParams({
          mode: accion.mode || "burbujas",
          variable: accion.variable || "visitantes",
          anio: accion.anio || 2024,
        });
        window.open(`geovisor.html?${params}`, "_self");
      } else {
        // Solo actualizar dashboard
        if (typeof renderDashboard === "function") renderDashboard();
      }
    }
  };

  // ── Form submit ────────────────────────────────────────────────────────────
  form.addEventListener("submit", e => {
    e.preventDefault();
    enviarMensaje(input.value);
  });

  // Enter = enviar, Shift+Enter = nueva línea
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      enviarMensaje(input.value);
    }
  });

  // Auto-resize textarea
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 120) + "px";
  });

  // ── Mensaje de bienvenida ─────────────────────────────────────────────────
  renderMensaje(
    "¡Hola! Soy el Asistente IA del Observatorio GeoTurismo.\n\nPuedo ayudarte a consultar datos de los 29 municipios del Valle del Cauca (2022-2025): visitantes, ocupación hotelera, atractivos, índice de oportunidad y más.\n\nTambién puedo navegar el dashboard y mostrar mapas por ti.",
    "bot"
  );

})();
