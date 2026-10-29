/* Plan de estudio · Contaduría Pública (Colombia) — interfaz */
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const SHORT = { CON: "Contabilidad", TRI: "Tributaria", AUD: "Auditoría", FIN: "Costos y finanzas", LEG: "Legal y laboral", FUN: "Fundamentos" };
const TIPO = { estudio: "Estudio", evaluacion: "Evaluación", repaso: "Repaso", manual: "Manual" };
const DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
const LEITNER = [0, 1, 3, 7, 14, 30];

const MODCOL = ["#2563eb", "#d97706", "#059669", "#7c3aed", "#dc2626", "#0891b2", "#db2777", "#65a30d"];
const ICON = {
  estudio: '<svg viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15zM4 20.5A2.5 2.5 0 0 0 6.5 23H20"/></svg>',
  evaluacion: '<svg viewBox="0 0 24 24"><path d="M9 11l3 3 8-8M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9"/></svg>',
  repaso: '<svg viewBox="0 0 24 24"><rect x="3" y="7" width="14" height="14" rx="2"/><path d="M7 3h12a2 2 0 0 1 2 2v12"/></svg>',
  manual: '<svg viewBox="0 0 24 24"><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>',
};
const FLAME = '<svg class="flame" viewBox="0 0 24 24"><path d="M12 2c1 4-3 5.5-3 9.5A4 4 0 0 0 13 15.5c0-1.5-1-2.3-.5-4 2.5 1.5 4.5 3.8 4.5 6.5a5 5 0 0 1-10 0C7 12 12 9 12 2z"/></svg>';

/* ------------------------------------------------------------------ tema (claro / oscuro / auto) */
function applyTheme() {
  let pref = "auto";
  try { pref = localStorage.getItem("tema") || "auto"; } catch (e) { /* sin almacenamiento */ }
  const dark = pref === "dark" || (pref === "auto" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  document.documentElement.dataset.pref = pref;
  document.querySelectorAll("[data-act=theme]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.v === pref)));
}
function setTheme(p) { try { localStorage.setItem("tema", p); } catch (e) { /* ignorar */ } applyTheme(); toast(p === "dark" ? "Modo oscuro activado" : p === "light" ? "Modo claro activado" : "Tema automático (sigue tu sistema)"); }
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applyTheme);

const S = { boot: null, stats: null, sched: null, openMods: new Set(), fcSetup: { scope: "due", id: "", limit: "20" }, fc: null, quiz: null, report: null, attempts: null, showAll: false, view: "inicio" };

async function api(path, body) {
  const opt = body !== undefined ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const r = await fetch("/api" + path, opt);
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || "Error de comunicación con el servidor");
  return d;
}
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast.t);
  toast.t = setTimeout(() => t.classList.remove("show"), 2600);
}
const num = (n, d = 1) => (n == null ? "—" : Number(n).toLocaleString("es-CO", { minimumFractionDigits: d, maximumFractionDigits: d }));
const pct = (n) => (n == null ? "—" : num(n, 0) + "%");
const fmtMin = (m) => { const h = Math.floor(m / 60), r = m % 60; return h ? `${h} h${r ? " " + r + " min" : ""}` : `${r} min`; };
const parseD = (iso) => new Date(iso + "T00:00:00");
const fmtD = (iso, o = { weekday: "short", day: "numeric", month: "short" }) => parseD(iso).toLocaleDateString("es-CO", o);
const areaOf = (id) => S.boot.areas.find((a) => a.id === id) || {};
const areaColor = (id) => areaOf(id).color || "var(--brand)";
const chip = (id) => `<span class="chip" style="--c:${areaColor(id)}">${esc(SHORT[id] || id)}</span>`;
const bar = (p, c) => `<div class="bar" role="img" aria-label="${pct(p)}"><i style="width:${Math.max(0, Math.min(100, p || 0))}%;${c ? "--c:" + c : ""}"></i></div>`;
const findSub = (sid) => { for (const m of S.boot.modules) for (const s of m.materias) if (s.id === sid) return s; return null; };

async function refresh(full = true) {
  const [b, st] = await Promise.all([api("/bootstrap"), api("/stats")]);
  S.boot = b; S.stats = st;
  if (full) render();
}

/* ------------------------------------------------------------------ router */
function render() {
  const parts = (location.hash || "#inicio").slice(1).split("/");
  const v = parts[0];
  S.route = parts;
  S.view = ["inicio", "plan", "clase", "flashcards", "evaluaciones", "cronograma", "talleres", "taller", "ajustes"].includes(v) ? v : "inicio";
  document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("on", a.dataset.v === (S.view === "clase" ? "plan" : S.view === "taller" ? "talleres" : S.view)));
  const fn = { inicio: vInicio, plan: vPlan, clase: vClase, flashcards: vFlash, evaluaciones: vEval, cronograma: vCrono, talleres: vTalleres, taller: vTaller, ajustes: vAjustes }[S.view];
  const key = location.hash || "#inicio", m = $("#main");
  m.classList.toggle("enter", key !== S.lastKey);
  S.lastKey = key;
  const html = fn();
  if (html && typeof html.then === "function") { html.then((h) => { m.innerHTML = h; postRender(); }); } else { m.innerHTML = html; postRender(); }
  const st = S.stats;
  $("#sidefoot").innerHTML = st ? `<span class="streak">${FLAME}<b>${st.racha}</b> día${st.racha === 1 ? "" : "s"} de racha</span><br>Progreso guardado en SQLite` : "";
  applyTheme();
}
function postRender() {
  const enter = $("#main").classList.contains("enter"), reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll("[data-count]").forEach((el) => {
    const v = parseFloat(el.dataset.count);
    if (!isFinite(v) || reduce || !(enter || el.dataset.always)) return;
    const dec = Number(el.dataset.dec || 0), t0 = performance.now(), dur = 800;
    const tick = (t) => { const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3); el.textContent = num(v * e, dec); if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  });
  if (S.confetti) { S.confetti = false; if (!reduce) confetti(); }
  if (S.quiz) S.quiz.fresh = false;
}
function confetti() {
  const box = document.createElement("div");
  box.className = "confetti";
  const cols = ["#2563eb", "#d97706", "#059669", "#7c3aed", "#dc2626", "#0891b2", "#db2777"];
  for (let i = 0; i < 70; i++) {
    const p = document.createElement("i");
    p.style.cssText = `left:${Math.random() * 100}%;background:${cols[i % cols.length]};--x:${(Math.random() - 0.5) * 240}px;--r:${Math.random() * 900 - 450}deg;--d:${2.2 + Math.random() * 1.8}s;--dl:${Math.random() * 0.6}s`;
    box.appendChild(p);
  }
  document.body.appendChild(box);
  setTimeout(() => box.remove(), 4800);
}
window.addEventListener("hashchange", () => { render(); window.scrollTo(0, 0); });

/* ------------------------------------------------------------------ INICIO */
function vInicio() {
  const st = S.stats;
  const nota = st.global == null ? "—" : num(st.global / 20);
  const umbral = S.boot.settings.umbral;
  const hoy = st.hoy.map(sessRow).join("") || `<p class="muted">No hay sesiones programadas para hoy. <a href="#cronograma">Configura tu cronograma</a>.</p>`;
  return `
  <section class="hero"><div><h1>Mi avance</h1><p>Resumen de tu preparación en Contaduría Pública.</p>
    <div class="hero-stats"><span>${FLAME}<b data-count="${st.racha}">${st.racha}</b> día${st.racha === 1 ? "" : "s"} de racha</span><span><b>${st.hoy.length}</b> sesión(es) hoy</span><span><b>${st.cards_due}</b> flashcards por repasar</span></div></div>
    ${(() => { const n = nextTopic(); return n ? `<a class="btn" href="#clase/${n.s.id}/${n.t.idx}">Continuar: ${esc(n.t.nombre)} →</a>` : ""; })()}</section>
  ${st.intento_activo ? `<div class="banner"><span>Tienes una evaluación en curso.</span><a class="btn sm pri" href="#evaluaciones" data-act="resume">Continuar evaluación</a></div>` : ""}
  ${st.atrasadas ? `<div class="banner bad"><span>${st.atrasadas} sesión(es) atrasada(s) en tu cronograma.</span><a class="btn sm" href="#cronograma">Revisar cronograma</a></div>` : ""}
  <div class="grid g4">
    <div class="card stat"><span>Nota global ponderada (0–5)</span><b data-count="${st.global == null ? "" : (st.global / 20).toFixed(1)}" data-dec="1">${nota}</b><span>${st.global == null ? "Aún sin evaluaciones" : pct(st.global) + " · meta " + umbral + "%"}</span></div>
    <div class="card stat"><span>Temas completados</span><b><span data-count="${st.temas_hechos}">${st.temas_hechos}</span>/${st.temas_total}</b>${bar(100 * st.temas_hechos / (st.temas_total || 1))}</div>
    <div class="card stat"><span>Horas de estudio</span><b>${num(st.horas_hechas, 0)}/${num(st.horas_total, 0)}</b>${bar(100 * st.horas_hechas / (st.horas_total || 1), "var(--ok)")}</div>
    <div class="card stat"><span>Flashcards por repasar hoy</span><b>${st.cards_due}</b><span>${st.cards_dominadas}/${st.cards_total} dominadas</span></div>
  </div>
  <div class="grid g2" style="margin-top:1rem">
    <section class="card"><h2>Dominio por área</h2><p class="muted small">Se calcula con el último resultado de cada pregunta, ponderado por su puntaje. El peso de cada área se configura en Ajustes.</p>
      <table><thead><tr><th>Área</th><th class="n">Peso</th><th style="width:34%">Dominio</th><th class="n">Resp.</th></tr></thead><tbody>
      ${st.areas.map((a) => `<tr><td>${chip(a.id)}</td><td class="n">${num(a.peso, 0)}%</td><td>${bar(a.mastery, a.color)}<span class="small muted">${pct(a.mastery)}</span></td><td class="n small">${a.answered}/${a.total}</td></tr>`).join("")}
      </tbody></table></section>
    <section class="card"><h2>Hoy en tu cronograma</h2>${hoy}
      <div class="row" style="margin-top:.8rem"><a class="btn sm pri" href="#flashcards" data-act="studydue">Repasar flashcards</a><a class="btn sm" href="#evaluaciones">Hacer una evaluación</a></div></section>
  </div>
  <section class="card" style="margin-top:1rem"><h2>Últimas evaluaciones</h2>
    ${st.attempts.length ? `<table><thead><tr><th>Alcance</th><th>Fecha</th><th class="n">Nota</th><th class="n">Ponderada</th><th></th></tr></thead><tbody>${st.attempts.map((a) => `<tr><td>${esc(a.scope_label)}</td><td>${fmtD(a.finished.slice(0, 10))}</td><td class="n"><b>${num(a.nota)}</b></td><td class="n">${pct(a.ponderada)}</td><td class="n"><button class="btn sm" data-act="viewattempt" data-id="${a.id}">Ver</button></td></tr>`).join("")}</tbody></table>` : `<p class="muted">Todavía no has presentado evaluaciones.</p>`}
  </section>`;
}
function titleLink(it) {
  return it.tipo === "estudio" && it.subject_id != null && it.topic_idx != null ? `<a href="#clase/${it.subject_id}/${it.topic_idx}">${esc(it.titulo)}</a>` : esc(it.titulo);
}
function nextTopic() {
  for (const m of S.boot.modules) for (const s of m.materias) for (const t of s.temas) if (!t.done) return { s, t, m };
  return null;
}
function sessCard(it, o = {}) {
  const col = it.area_id ? areaColor(it.area_id) : "var(--muted)";
  const done = it.status === "done", late = it.status === "pending" && it.fecha < S.boot.today;
  return `<div class="scard ${done ? "done" : ""} ${late ? "late" : ""}" style="--c:${col};--i:${o.i || 0}">
    <span class="sico">${ICON[it.tipo] || ICON.manual}</span>
    <div class="sbody"><div class="stitle">${titleLink(it)}</div>
      <div class="smeta"><span class="badge">${TIPO[it.tipo] || it.tipo}</span><span>${fmtMin(it.minutos)}</span>${it.partes > 1 ? `<span>parte ${it.parte}/${it.partes}</span>` : ""}${late ? '<span class="badge bad">Atrasada</span>' : ""}${o.date ? `<input type="date" class="mv" value="${it.fecha}" data-chg="movesess" data-id="${it.id}" aria-label="Reprogramar sesión" title="Reprogramar">` : ""}</div></div>
    ${o.del ? `<button class="btn sm danger" data-act="delsess" data-id="${it.id}">Quitar</button>` : ""}
    <label class="tick" title="Marcar como hecha"><input type="checkbox" data-chg="sess" data-id="${it.id}" ${done ? "checked" : ""} aria-label="Marcar como hecha"><span class="box"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span></label></div>`;
}
const sessRow = (it, i) => sessCard(it, { i });

/* ------------------------------------------------------------------ PLAN */
function vPlan() {
  const mods = S.boot.modules;
  return `<div class="head"><div><h1>Plan de estudio</h1><p>${mods.length} módulos · ${mods.reduce((n, m) => n + m.materias.length, 0)} materias. Marca los temas que ya estudiaste; el cronograma y tu avance se actualizan.</p></div>
    <div class="row"><button class="btn sm" data-act="expandall">Expandir todo</button><button class="btn sm" data-act="collapseall">Contraer todo</button></div></div>
  ${mods.map((m) => {
    const tt = m.materias.reduce((n, s) => n + s.temas.length, 0), td = m.materias.reduce((n, s) => n + s.temas.filter((t) => t.done).length, 0);
    const hh = m.materias.reduce((n, s) => n + s.horas, 0);
    const mp = Math.round(100 * td / (tt || 1));
    return `<details class="card mod" style="--mc:${MODCOL[(m.orden - 1) % MODCOL.length]}" data-mod="${m.id}" ${S.openMods.has(m.id) ? "open" : ""}><summary>
      <div><h2>${m.orden}. ${esc(m.titulo)}</h2><span class="muted small">${esc(m.semestres)} · ${esc(m.descripcion)}</span></div>
      <div class="msum"><div class="small"><b>${td}/${tt}</b> temas · ${num(hh, 0)} h<br>dominio ${pct(m.mastery)}</div><div class="ringc" style="--p:${mp}"><span>${mp}%</span></div></div></summary>
      <div class="subs">${m.materias.map(subCard).join("")}</div></details>`;
  }).join("")}`;
}
function subCard(s) {
  const done = s.temas.filter((t) => t.done).length;
  return `<article class="sub"><div class="row" style="justify-content:space-between">${chip(s.area_id)}<span class="small muted">${num(s.horas, 0)} h · ${done}/${s.temas.length} temas</span></div>
    <h3>${esc(s.nombre)}</h3><p class="muted small" style="margin:0">${esc(s.descripcion)}</p>
    <div>${s.temas.map((t) => `<div class="topic ${t.done ? "done" : ""}"><input type="checkbox" data-chg="topic" data-sid="${s.id}" data-idx="${t.idx}" ${t.done ? "checked" : ""} aria-label="Marcar tema como estudiado"><a class="t" href="#clase/${s.id}/${t.idx}">${esc(t.nombre)}</a><span class="small muted" style="margin-left:auto">${num(t.horas, 0)} h</span></div>`).join("")}</div>
    <div class="row small"><span class="badge ${s.mastery == null ? "" : s.mastery >= S.boot.settings.umbral ? "ok" : "warn"}">Dominio ${pct(s.mastery)}</span><span class="muted">${s.n_cards} flashcards · ${s.n_questions} preguntas</span></div>
    <div class="row"><a class="btn sm" href="#clase/${s.id}/0">Clases</a><button class="btn sm" data-act="fcsub" data-id="${s.id}">Flashcards</button><button class="btn sm pri" data-act="quizsub" data-id="${s.id}">Evaluar</button></div>
    <details class="note" ${s.nota ? "open" : ""}><summary>Mis notas</summary><textarea rows="3" data-note="${s.id}" placeholder="Escribe tus apuntes, dudas o artículos clave…">${esc(s.nota)}</textarea></details></article>`;
}

/* ------------------------------------------------------------------ CLASES */
function inl(s) {
  s = esc(s);
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s).,;:]|$)/g, "$1<em>$2</em>");
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  return s;
}
function md(src) {
  const L = String(src || "").replace(/\r/g, "").split("\n");
  let h = "", i = 0;
  const isBlock = (l) => /^(#{2,4}\s|\||>|[-*]\s+|\d+\.\s+)/.test(l);
  while (i < L.length) {
    const l = L[i];
    if (!l.trim()) { i++; continue; }
    let m;
    if ((m = l.match(/^(#{2,4})\s+(.*)/))) { h += `<h${m[1].length}>${inl(m[2])}</h${m[1].length}>`; i++; continue; }
    if (l.startsWith("|")) {
      const rows = [];
      while (i < L.length && L[i].startsWith("|")) { rows.push(L[i]); i++; }
      const cells = (r) => r.replace(/^\||\|\s*$/g, "").split("|").map((c) => c.trim());
      const body = rows.filter((r) => !/^\|?\s*:?-{2,}/.test(r));
      h += `<div class="tbl"><table><thead><tr>${cells(body[0]).map((c) => `<th>${inl(c)}</th>`).join("")}</tr></thead><tbody>${body.slice(1).map((r) => `<tr>${cells(r).map((c) => `<td>${inl(c)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
      continue;
    }
    if (l.startsWith(">")) {
      const parts = [];
      while (i < L.length && L[i].startsWith(">")) { parts.push(L[i].replace(/^>\s?/, "")); i++; }
      h += `<blockquote>${parts.join("\n").split(/\n\s*\n|\n(?=[-*]\s)/).map((p) => inl(p.trim()).replace(/\n/g, "<br>")).filter(Boolean).map((p) => `<p>${p}</p>`).join("")}</blockquote>`;
      continue;
    }
    if (/^[-*]\s+/.test(l)) { const it = []; while (i < L.length && /^[-*]\s+/.test(L[i])) { it.push(L[i].replace(/^[-*]\s+/, "")); i++; } h += `<ul>${it.map((x) => `<li>${inl(x)}</li>`).join("")}</ul>`; continue; }
    if (/^\d+\.\s+/.test(l)) { const it = []; while (i < L.length && /^\d+\.\s+/.test(L[i])) { it.push(L[i].replace(/^\d+\.\s+/, "")); i++; } h += `<ol>${it.map((x) => `<li>${inl(x)}</li>`).join("")}</ol>`; continue; }
    const par = [];
    while (i < L.length && L[i].trim() && !isBlock(L[i])) { par.push(L[i]); i++; }
    h += `<p>${inl(par.join(" "))}</p>`;
  }
  return h;
}
const RTIPO = { video: "Video", articulo: "Lectura", norma: "Norma", curso: "Curso", herramienta: "Herramienta" };
function resList(list) {
  return list.map((r) => `<a class="res" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer"><span class="badge ${r.tipo === "video" ? "bad" : r.tipo === "norma" ? "warn" : ""}">${RTIPO[r.tipo] || "Enlace"}</span><span><b>${esc(r.titulo)}</b><small>${esc(r.fuente)}</small></span></a>`).join("");
}
async function vClase() {
  const sid = S.route[1], idx = Number(S.route[2] || 0);
  let t;
  try { t = await api(`/lesson?subject=${encodeURIComponent(sid)}&idx=${idx}`); } catch (e) { return `<div class="pad"><p>${esc(e.message)}</p><a class="btn" href="#plan">Volver al plan</a></div>`; }
  const seen = new Set(t.recursos.map((r) => r.url));
  t.recursos_materia = t.recursos_materia.filter((r) => !seen.has(r.url));
  const tl = (S.tall || (await loadTalleres())).filter((x) => x.subject_id === sid);
  const prev = idx > 0 ? idx - 1 : null, next = idx + 1 < t.total_temas ? idx + 1 : null;
  return `<p class="small muted"><a href="#plan">Plan</a> › ${esc(t.modulo)} › ${esc(t.materia)}</p>
  <div class="lesson"><article class="card prose">
    <div class="row" style="justify-content:space-between">${chip(t.area_id)}<span class="small muted">Tema ${idx + 1} de ${t.total_temas} · ${num(t.horas, 0)} h de estudio</span></div>
    <h1>${esc(t.nombre)}</h1>
    ${t.clase ? md(t.clase) : `<p class="muted">Esta clase aún no tiene contenido escrito. Usa los recursos y las flashcards de la materia.</p>`}
    <hr>
    <div class="row"><button class="btn ${t.done ? "" : "pri"}" data-act="lessondone" data-sid="${sid}" data-idx="${idx}" data-done="${t.done ? 0 : 1}">${t.done ? "Desmarcar como estudiado" : "Marcar como estudiado"}</button>
      ${prev != null ? `<a class="btn" href="#clase/${sid}/${prev}">← Anterior</a>` : ""}${next != null ? `<a class="btn" href="#clase/${sid}/${next}">Siguiente tema →</a>` : `<button class="btn" data-act="quizsub" data-id="${sid}">Evaluar la materia</button>`}</div>
  </article>
  <aside class="grid" style="align-content:start">
    <section class="card"><h3>Recursos de este tema</h3>${t.recursos.length ? `<div class="reslist">${resList(t.recursos)}</div>` : `<p class="muted small">Sin recursos específicos.</p>`}</section>
    ${t.recursos_materia.length ? `<section class="card"><h3>Para profundizar en la materia</h3><div class="reslist">${resList(t.recursos_materia)}</div></section>` : ""}
    ${tl.length ? `<section class="card"><h3>Practica con talleres</h3>${tl.map((x) => `<a class="res" href="#taller/${x.id}"><span class="badge ${x.tipo === "excel" ? "ok" : "warn"}">${x.tipo === "excel" ? "Excel" : "Trabajo"}</span><span><b>${esc(x.titulo)}</b><small>${fmtMin(x.minutos)} · ${ESTADO_T[x.estado][1]}</small></span></a>`).join("")}</section>` : ""}
    <section class="card"><h3>Temas de la materia</h3><ol class="toc">${t.temas.map((x) => `<li class="${x.idx === idx ? "cur" : ""}"><a href="#clase/${sid}/${x.idx}">${esc(x.nombre)}</a></li>`).join("")}</ol>
      <div class="row"><button class="btn sm" data-act="fcsub" data-id="${sid}">Flashcards (${t.n_cards})</button><button class="btn sm pri" data-act="quizsub" data-id="${sid}">Evaluar</button></div></section>
  </aside></div>`;
}

/* ------------------------------------------------------------------ TALLERES */
const ESTADO_T = { pendiente: ["", "Pendiente"], entregado: ["warn", "Entregado · sin calificar"], calificado: ["ok", "Calificado"] };
async function loadTalleres() { S.tall = (await api("/talleres")).talleres; return S.tall; }
async function vTalleres() {
  const list = S.tall || (await loadTalleres());
  const f = S.tfilter || "todos";
  const vis = list.filter((t) => f === "todos" || (f === "excel" && t.tipo === "excel") || (f === "trabajo" && t.tipo !== "excel") || f === t.estado);
  const done = list.filter((t) => t.estado === "calificado").length;
  const notas = list.filter((t) => t.mejor_nota != null).map((t) => t.mejor_nota);
  const prom = notas.length ? notas.reduce((a, b) => a + b, 0) / notas.length : null;
  const opt = (v, l) => `<option value="${v}" ${f === v ? "selected" : ""}>${l}</option>`;
  return `<div class="pagehead"><h1>Talleres</h1><p class="muted">Ejercicios para practicar en Excel (libros contables, nómina, costos, impuestos, auditoría…) y trabajos escritos. Descarga la plantilla, resuélvelo, súbelo aquí para una autorrevisión inmediata y pide a Claude que lo revise y califique.</p></div>
  <div class="grid cols3" style="margin-bottom:1rem">
    <div class="card stat"><span class="muted small">Talleres calificados</span><b><span data-count="${done}" data-dec="0">${done}</span> / ${list.length}</b></div>
    <div class="card stat"><span class="muted small">Promedio de notas (0–5)</span><b>${prom == null ? "—" : num(prom, 1)}</b></div>
    <div class="card stat"><span class="muted small">Entregados</span><b>${list.filter((t) => t.entregas).length}</b></div>
  </div>
  <div class="row" style="margin-bottom:1rem"><label class="small muted">Mostrar <select data-chg="tfilter">${opt("todos", "Todos")}${opt("excel", "Solo Excel")}${opt("trabajo", "Solo trabajos escritos")}${opt("pendiente", "Pendientes")}${opt("entregado", "Sin calificar")}${opt("calificado", "Calificados")}</select></label></div>
  <div class="grid cols2">${vis.map((t) => {
    const [cl, lb] = ESTADO_T[t.estado];
    return `<a class="card tcard" href="#taller/${t.id}"><div class="row" style="justify-content:space-between"><span class="badge ${t.tipo === "excel" ? "ok" : "warn"}">${t.tipo === "excel" ? "Excel" : "Trabajo escrito"}</span><span class="badge ${cl}">${lb}</span></div>
      <h3>${esc(t.titulo)}</h3><p class="small muted">${esc(t.objetivo)}</p>
      <div class="row small muted"><span>${esc(t.nivel)}</span><span>·</span><span>${fmtMin(t.minutos)}</span><span>·</span><span>${esc(t.materia)}</span></div>
      ${t.entregas ? `<div class="row small"><b>${t.mejor_nota != null ? "Nota Claude: " + num(t.mejor_nota, 1) + " / 5" : "Esperando calificación"}</b>${t.mejor_auto != null ? `<span class="muted">· autorrevisión ${num(t.mejor_auto, 0)}%</span>` : ""}</div>` : ""}</a>`;
  }).join("") || `<p class="muted">No hay talleres con ese filtro.</p>`}</div>`;
}
function tallerPrompt(t) {
  const rub = t.rubrica.map((r) => `- ${r.criterio} (${r.puntos} pts): ${r.detalle}`).join("\n");
  return `Actúa como profesor de Contaduría Pública en Colombia. Voy a adjuntarte mi entrega del taller «${t.titulo}» (${t.tipo === "excel" ? "archivo de Excel" : "documento escrito"}). Revísala con rigor y califícala.

ENUNCIADO
${t.enunciado}

QUÉ DEBÍA ENTREGAR
${t.entrega}

RÚBRICA (total 100 pts)
${rub}

Por favor responde con: (1) nota de 0 a 5 y puntaje por criterio de la rúbrica, (2) errores concretos (indica hoja/celda o párrafo) y cómo corregirlos, (3) qué hice bien, (4) qué debo repasar. Si algún cálculo está mal, muéstrame el procedimiento correcto.`;
}
async function vTaller() {
  const id = S.route[1];
  let t;
  try { t = await api(`/taller?id=${encodeURIComponent(id)}${S.treveal === id ? "&reveal=1" : ""}`); } catch (e) { return `<div class="pad"><p>${esc(e.message)}</p><a class="btn" href="#talleres">Volver</a></div>`; }
  S.cur = t;
  const ult = t.entregas[0];
  const auto = (e) => {
    const a = e.auto_detail;
    if (!a) return e.filename.toLowerCase().endsWith(".xlsx") ? "" : `<p class="small muted">Este tipo de archivo no tiene autorrevisión; pide la revisión a Claude.</p>`;
    if (!a.ok) return `<p class="small" style="color:var(--bad)">${esc(a.error)}</p>`;
    return `<div class="row"><b>Autorrevisión: ${num(a.score, 0)}%</b><span class="muted small">(${num(a.ganados, 0)} de ${num(a.total, 0)} pts de verificación)</span></div>${bar(a.score)}
      ${a.aviso ? `<p class="small" style="color:var(--warn)">${esc(a.aviso)}</p>` : ""}
      <ul class="chk">${a.detalle.map((d) => `<li class="${d.ok ? "ok" : "no"}"><span>${d.ok ? "✓" : "✗"}</span><span>${esc(d.desc)} <small class="muted">(${d.puntos} pts)</small>${d.ok ? "" : `<small class="muted"> — ${esc(d.nota || d.pista)}</small>`}</span></li>`).join("")}</ul>
      <p class="small muted">Es una vista previa automática: solo busca los resultados clave en tu libro. La calificación definitiva es la revisión de Claude.</p>`;
  };
  return `<p class="small muted"><a href="#talleres">Talleres</a> › ${esc(t.materia)}</p>
  <div class="lesson"><article class="card prose">
    <div class="row" style="justify-content:space-between"><span class="badge ${t.tipo === "excel" ? "ok" : "warn"}">${t.tipo === "excel" ? "Taller de Excel" : "Trabajo escrito"}</span><span class="small muted">${esc(t.nivel)} · ${fmtMin(t.minutos)}</span></div>
    <h1>${esc(t.titulo)}</h1>
    <p><b>Objetivo:</b> ${esc(t.objetivo)}</p>
    ${md(t.enunciado)}
    <h2>Qué debes entregar</h2>${md(t.entrega)}
    <h2>Rúbrica de calificación</h2>
    <div class="tbl"><table><thead><tr><th>Criterio</th><th>Pts</th><th>Qué se evalúa</th></tr></thead><tbody>${t.rubrica.map((r) => `<tr><td><b>${esc(r.criterio)}</b></td><td>${r.puntos}</td><td>${esc(r.detalle)}</td></tr>`).join("")}</tbody></table></div>
  </article>
  <aside class="grid" style="align-content:start">
    <section class="card"><h3>1 · Prepárate</h3>
      ${t.plantilla ? `<a class="btn pri" href="/plantillas/${t.plantilla}" download>Descargar plantilla .xlsx</a><p class="small muted">Incluye los datos y las hojas vacías. Resuélvelo con fórmulas.</p>` : `<p class="small muted">Redáctalo en Word, Google Docs o PDF.</p>`}</section>
    <section class="card"><h3>2 · Sube tu entrega</h3>
      <input type="file" id="tfile" accept="${t.tipo === "excel" ? ".xlsx" : ".pdf,.docx,.doc,.txt,.md,.xlsx"}">
      <div class="row" style="margin-top:.6rem"><button class="btn pri" data-act="tupload" data-id="${t.id}">Subir y revisar</button></div>
      <p class="small muted">Se guarda en tu carpeta <code>data/entregas</code>. Puedes entregar varias veces.</p></section>
    <section class="card"><h3>3 · Que Claude la califique</h3>
      <p class="small muted">Copia la solicitud y pégala en un chat con Claude adjuntando tu archivo (o súbelo en esta misma sesión). Luego registra aquí la nota.</p>
      <div class="row"><button class="btn" data-act="tcopy">Copiar solicitud de revisión</button></div>
      <textarea id="tprompt" class="hidden" readonly rows="6" style="width:100%;margin-top:.5rem"></textarea>
      <div class="gform"><label class="small muted">Nota de Claude (0–5)<input type="number" id="tnota" min="0" max="5" step="0.1" value="${ult && ult.claude_nota != null ? ult.claude_nota : ""}"></label>
      <label class="small muted">Comentarios / retroalimentación<textarea id="tcom" rows="4" placeholder="Pega aquí la retroalimentación de Claude">${ult && ult.claude_comentarios ? esc(ult.claude_comentarios) : ""}</textarea></label>
      <button class="btn sm pri" data-act="tgrade" data-id="${t.id}" ${ult ? "" : "disabled"}>Guardar calificación</button></div></section>
  </aside></div>
  ${t.entregas.length ? `<h2 style="margin-top:1.5rem">Tus entregas</h2><div class="grid">${t.entregas.map((e) => `<section class="card"><div class="row" style="justify-content:space-between"><b>${esc(e.filename)}</b><span class="small muted">${esc(e.fecha.replace("T", " "))}</span></div>
    ${auto(e)}
    ${e.claude_nota != null ? `<div class="callout"><b>Nota de Claude: ${num(e.claude_nota, 1)} / 5</b>${e.claude_comentarios ? `<div class="small" style="white-space:pre-wrap;margin-top:.4rem">${esc(e.claude_comentarios)}</div>` : ""}</div>` : ""}
    <div class="row"><button class="btn sm danger" data-act="tdel" data-id="${e.id}">Eliminar entrega</button></div></section>`).join("")}</div>` : ""}
  ${t.tipo === "excel" && t.checks.length ? `<section class="card" style="margin-top:1rem"><h3>Resultados de control</h3>${t.revelado ? `<ul class="chk">${t.checks.map((c) => `<li class="ok"><span>•</span><span>${esc(c.desc)}${c.value != null ? ` = <b>${Number(c.value).toLocaleString("es-CO", { maximumFractionDigits: 2 })}</b>` : ""} <small class="muted">${c.pista ? "— " + esc(c.pista) : ""}</small></span></li>`).join("")}</ul>` : t.puede_revelar ? `<p class="small muted">Ya entregaste: puedes ver los valores correctos para comparar.</p><button class="btn sm" data-act="treveal" data-id="${t.id}">Ver respuestas de control</button>` : `<p class="small muted">Se desbloquean después de tu primera entrega, para que primero lo intentes tú.</p>`}</section>` : ""}`;
}
async function tUpload(id) {
  const f = $("#tfile").files[0];
  if (!f) { toast("Elige primero un archivo"); return; }
  if (f.size > 15 * 1024 * 1024) { toast("El archivo supera 15 MB"); return; }
  const buf = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(f); });
  const r = await api("/taller/entrega", { id, filename: f.name, data: String(buf).split(",")[1] });
  S.tall = null; S.stats = (await api("/stats"));
  toast(r.auto && r.auto.ok ? `Entrega guardada · autorrevisión ${num(r.auto.score, 0)}%` : "Entrega guardada");
  render();
}

/* ------------------------------------------------------------------ FLASHCARDS */
function rateHints(card) {
  const b = card.box || 0;
  const d = (x) => { const n = LEITNER[Math.min(5, x)]; return n === 0 ? "hoy" : n + " d"; };
  return [["Otra vez", "hoy"], ["Difícil", d(Math.max(1, b))], ["Bien", d(b + 1)], ["Fácil", d(b + 2)]];
}
function vFlash() {
  const f = S.fc;
  if (f && f.queue) {
    if (f.i >= f.queue.length) {
      const r = f.stats;
      return `<div class="head"><div><h1>Sesión terminada</h1></div></div><div class="card" style="max-width:560px"><p class="score">${f.total}</p><p>tarjetas revisadas</p>
        <p class="muted">Otra vez: ${r[0]} · Difícil: ${r[1]} · Bien: ${r[2]} · Fácil: ${r[3]}</p>
        <div class="row"><button class="btn pri" data-act="fcend">Volver</button></div></div>`;
    }
    const c = f.queue[f.i];
    return `<div class="head"><div><h1>Flashcards</h1><p>${f.i + 1} de ${f.queue.length} · ${esc(c.materia)}</p></div><button class="btn sm" data-act="fcend">Salir de la sesión</button></div>
      ${bar(100 * f.i / f.queue.length)}
      <div class="fcwrap ${f.flip ? "flipped" : ""}" id="fcwrap" style="margin-top:1rem"><button class="flash" data-act="flip" aria-label="Voltear tarjeta"><div class="inner">
        <div class="face front"><div class="row">${chip(c.area_id)}${c.origin === "user" ? '<span class="badge">Mía</span>' : ""}</div>
          <div class="q">${esc(c.front)}</div><div class="hint">Toca la tarjeta o presiona Espacio para ver la respuesta</div></div>
        <div class="face back"><div class="row">${chip(c.area_id)}<span class="small muted">${esc(c.front)}</span></div>
          <div class="a">${esc(c.back)}</div>${c.nota ? `<div class="nota"><b>Nota relevante:</b> ${esc(c.nota)}</div>` : ""}</div>
      </div></button>
      <div class="rate">${rateHints(c).map((h, i) => `<button class="btn ${i === 2 ? "pri" : ""}" data-act="rate" data-r="${i}">${h[0]}<small>${h[1]} · tecla ${i + 1}</small></button>`).join("")}</div></div>`;
  }
  const su = S.fcSetup;
  const mods = S.boot.modules;
  const target = su.scope === "subject" ? `<label class="f">Materia<select data-chg="fcsetup" data-k="id">${mods.map((m) => `<optgroup label="${esc(m.titulo)}">${m.materias.map((s) => `<option value="${s.id}" ${su.id === s.id ? "selected" : ""}>${esc(s.nombre)}</option>`).join("")}</optgroup>`).join("")}</select></label>`
    : su.scope === "module" ? `<label class="f">Módulo<select data-chg="fcsetup" data-k="id">${mods.map((m) => `<option value="${m.id}" ${su.id === m.id ? "selected" : ""}>${esc(m.titulo)}</option>`).join("")}</select></label>`
    : su.scope === "area" ? `<label class="f">Área<select data-chg="fcsetup" data-k="id">${S.boot.areas.map((a) => `<option value="${a.id}" ${su.id === a.id ? "selected" : ""}>${esc(a.nombre)}</option>`).join("")}</select></label>` : "";
  const own = S.myCards || [];
  return `<div class="head"><div><h1>Flashcards</h1><p>Repetición espaciada (método Leitner): lo que fallas vuelve pronto; lo que dominas, cada vez más espaciado.</p></div></div>
  <div class="grid g2"><section class="card"><h2>Nueva sesión</h2><div class="cfg">
    <label class="f">¿Qué quieres repasar?<select data-chg="fcsetup" data-k="scope">
      <option value="due" ${su.scope === "due" ? "selected" : ""}>Pendientes de hoy (${S.stats.cards_due})</option><option value="subject" ${su.scope === "subject" ? "selected" : ""}>Una materia</option>
      <option value="module" ${su.scope === "module" ? "selected" : ""}>Un módulo</option><option value="area" ${su.scope === "area" ? "selected" : ""}>Un área</option><option value="all" ${su.scope === "all" ? "selected" : ""}>Todas</option></select></label>
    ${target}
    <label class="f">Cantidad máxima<select data-chg="fcsetup" data-k="limit">${["10", "20", "50", "0"].map((n) => `<option value="${n}" ${su.limit === n ? "selected" : ""}>${n === "0" ? "Todas las disponibles" : n}</option>`).join("")}</select></label>
    <button class="btn pri" data-act="fcstart">Comenzar</button></div></section>
  <section class="card"><h2>Crear mi propia flashcard</h2><div class="cfg">
    <label class="f">Materia<select id="nc-sub">${mods.map((m) => `<optgroup label="${esc(m.titulo)}">${m.materias.map((s) => `<option value="${s.id}">${esc(s.nombre)}</option>`).join("")}</optgroup>`).join("")}</select></label>
    <label class="f">Pregunta / concepto<input id="nc-front" maxlength="300"></label>
    <label class="f">Respuesta<textarea id="nc-back" rows="2"></textarea></label>
    <label class="f">Nota relevante (opcional)<input id="nc-nota" maxlength="300"></label>
    <button class="btn" data-act="fccreate">Guardar flashcard</button></div>
    ${own.length ? `<h3 style="margin-top:1rem">Mis flashcards (${own.length})</h3>${own.map((c) => `<div class="sess"><span class="tt">${esc(c.front)}</span><button class="btn sm danger" data-act="fcdel" data-id="${c.id}">Eliminar</button></div>`).join("")}` : ""}</section></div>`;
}
async function loadMyCards() { S.myCards = (await api("/flashcards")).filter((c) => c.origin === "user"); }
async function fcStart() {
  const su = S.fcSetup, p = new URLSearchParams({ shuffle: "1" });
  if (su.scope === "due") p.set("due", "1");
  else if (su.scope !== "all") { const id = su.id || firstId(su.scope); p.set(su.scope, id); }
  if (su.limit !== "0") p.set("limit", su.limit);
  const cards = await api("/flashcards?" + p);
  if (!cards.length) return toast("No hay tarjetas para esta selección. ¡Buen trabajo!");
  S.fc = { queue: cards, i: 0, flip: false, total: 0, stats: [0, 0, 0, 0] };
  render();
}
function firstId(scope) { return scope === "subject" ? S.boot.modules[0].materias[0].id : scope === "module" ? S.boot.modules[0].id : S.boot.areas[0].id; }
function doFlip() { S.fc.flip = !S.fc.flip; const w = $("#fcwrap"); if (w) w.classList.toggle("flipped", S.fc.flip); }
async function rate(r) {
  const f = S.fc, c = f.queue[f.i];
  try { await api("/flashcards/review", { card_id: c.id, rating: r }); } catch (e) { return toast(e.message); }
  f.stats[r]++; f.total++;
  if (r === 0) f.queue.push({ ...c });
  f.i++; f.flip = false;
  render();
}

/* ------------------------------------------------------------------ EVALUACIONES */
function vEval() {
  if (S.report) return reportHTML(S.report);
  if (S.quiz) return quizHTML();
  return evalSetup();
}
function evalSetup() {
  const su = S.evSetup || (S.evSetup = { scope: "subject", id: "", n: "0" });
  const mods = S.boot.modules;
  const sel = su.scope === "subject" ? `<label class="f">Materia<select data-chg="evsetup" data-k="id">${mods.map((m) => `<optgroup label="${esc(m.titulo)}">${m.materias.map((s) => `<option value="${s.id}" ${su.id === s.id ? "selected" : ""}>${esc(s.nombre)} (${s.n_questions})</option>`).join("")}</optgroup>`).join("")}</select></label>`
    : su.scope === "module" ? `<label class="f">Módulo<select data-chg="evsetup" data-k="id">${mods.map((m) => `<option value="${m.id}" ${su.id === m.id ? "selected" : ""}>${esc(m.titulo)}</option>`).join("")}</select></label>`
    : su.scope === "area" ? `<label class="f">Área<select data-chg="evsetup" data-k="id">${S.boot.areas.map((a) => `<option value="${a.id}" ${su.id === a.id ? "selected" : ""}>${esc(a.nombre)}</option>`).join("")}</select></label>` : "";
  const hist = (S.attempts || []).filter((a) => a.status === "finalizada");
  const active = S.stats.intento_activo;
  return `<div class="head"><div><h1>Evaluaciones</h1><p>Cada pregunta vale 1, 2 o 3 puntos según su dificultad. La nota final pondera además el peso de cada área (configurable en Ajustes).</p></div></div>
  ${active ? `<div class="banner"><span>Tienes una evaluación sin terminar.</span><span class="row"><button class="btn sm pri" data-act="resume">Continuar</button><button class="btn sm" data-act="discard" data-id="${active}">Descartar</button></span></div>` : ""}
  <section class="card" style="max-width:640px"><h2>Nueva evaluación</h2><div class="cfg">
    <label class="f">Tipo<select data-chg="evsetup" data-k="scope"><option value="subject" ${su.scope === "subject" ? "selected" : ""}>Por materia</option><option value="module" ${su.scope === "module" ? "selected" : ""}>Por módulo</option><option value="area" ${su.scope === "area" ? "selected" : ""}>Por área</option><option value="all" ${su.scope === "all" ? "selected" : ""}>Simulacro general (todas las áreas)</option></select></label>
    ${sel}
    <label class="f">Número de preguntas<select data-chg="evsetup" data-k="n"><option value="0" ${su.n === "0" ? "selected" : ""}>Automático</option>${[5, 10, 15, 20, 30].map((n) => `<option ${su.n === String(n) ? "selected" : ""}>${n}</option>`).join("")}</select></label>
    <p class="muted small" style="margin:0">Se priorizan las preguntas que nunca has respondido o que fallaste la última vez. Verás la retroalimentación después de cada respuesta.</p>
    <button class="btn pri" data-act="evstart">Comenzar evaluación</button></div></section>
  <section class="card" style="margin-top:1rem"><h2>Historial</h2>${hist.length ? `<table><thead><tr><th>Alcance</th><th>Fecha</th><th class="n">Puntos</th><th class="n">Nota</th><th class="n">Ponderada</th><th></th></tr></thead><tbody>
    ${hist.map((a) => `<tr><td>${esc(a.scope_label)}</td><td>${fmtD(a.finished.slice(0, 10))}</td><td class="n">${num(a.puntos, 0)}/${num(a.max_puntos, 0)}</td><td class="n"><b>${num(a.nota)}</b></td><td class="n">${pct(a.ponderada)}</td><td class="n"><button class="btn sm" data-act="viewattempt" data-id="${a.id}">Ver</button></td></tr>`).join("")}</tbody></table>` : `<p class="muted">Aún no hay evaluaciones terminadas.</p>`}</section>`;
}
function quizHTML() {
  const q = S.quiz, it = q.questions[q.idx];
  const done = q.questions.filter((x) => x.chosen != null);
  const pts = done.reduce((n, x) => n + (x.puntos || 0), 0), max = done.reduce((n, x) => n + x.peso, 0);
  const answered = it.chosen != null;
  return `<div class="head"><div><h1>${esc(q.attempt.scope_label)}</h1><p>Pregunta ${q.idx + 1} de ${q.questions.length} · Puntaje parcial: ${num(pts, 0)}/${num(max, 0)}</p></div><button class="btn sm" data-act="evpause">Guardar y salir</button></div>
  ${bar(100 * done.length / q.questions.length)}
  <section class="card${q.fresh ? " qin" : ""}" style="margin-top:1rem;max-width:780px"><div class="row" style="margin-bottom:.6rem">${chip(it.area)}<span class="badge warn">Vale ${it.peso} punto${it.peso > 1 ? "s" : ""}</span><span class="small muted">${esc(it.materia)}</span></div>
    <h2 style="margin-bottom:1rem">${esc(it.enunciado)}</h2>
    ${it.opciones.map((o, i) => {
      let cls = "";
      if (answered) cls = i === it.correcta ? "right" : i === it.chosen ? "wrong" : "";
      else if (q.sel === i) cls = "sel";
      return `<button class="opt ${cls}" data-act="opt" data-i="${i}" ${answered ? "disabled" : ""}><span class="k">${"ABCD"[i]}</span><span>${esc(o)}</span></button>`;
    }).join("")}
    ${answered ? `<div class="fb ${it.correct ? "ok" : "bad"}">${it.correct ? `<span class="plus">+${it.puntos}</span>` : ""}<b>${it.correct ? `Correcto · +${it.puntos} punto${it.puntos > 1 ? "s" : ""}` : "Incorrecto · 0 puntos"}</b><p>${esc(it.retro)}</p></div>
      <button class="btn pri" data-act="next">${q.idx + 1 < q.questions.length ? "Siguiente pregunta" : "Ver resultados"}</button>`
      : `<button class="btn pri" data-act="confirm" ${q.sel == null ? "disabled" : ""}>Confirmar respuesta</button><span class="small muted" style="margin-left:.6rem">Atajos: 1–4 para elegir, Enter para confirmar</span>`}
  </section>`;
}
function reportHTML(d) {
  const a = d.attempt, r = a.resumen, areas = S.boot.areas;
  const present = Object.keys(r.areas), sumW = present.reduce((n, k) => n + (areaOf(k).peso || 0), 0) || 1;
  const cls = r.aprobado ? "ok" : r.nivel === "En desarrollo" ? "warn" : "bad";
  return `<div class="head"><div><h1>Resultados</h1><p>${esc(a.scope_label)} · ${fmtD(a.finished.slice(0, 10), { day: "numeric", month: "long", year: "numeric" })}</p></div><button class="btn pri" data-act="repdone">Cerrar</button></div>
  <div class="grid g3"><div class="card stat"><span>Nota (0–5)</span><div class="ring"><svg viewBox="0 0 120 120"><circle class="rb" cx="60" cy="60" r="52"/><circle class="rf ${cls}" cx="60" cy="60" r="52" style="--off:${(326.7 * (1 - Math.min(100, a.ponderada || 0) / 100)).toFixed(1)}"/></svg><p class="score" data-count="${a.nota}" data-dec="1" data-always="1">${num(a.nota)}</p></div><span class="badge ${cls}">${esc(r.nivel)}</span></div>
    <div class="card stat"><span>Puntaje por peso de preguntas</span><p class="score">${num(a.puntos, 0)}<small style="font-size:1.1rem">/${num(a.max_puntos, 0)}</small></p><span>${pct(a.score_pct)} de los puntos posibles</span></div>
    <div class="card stat"><span>Nota ponderada por áreas</span><p class="score">${pct(a.ponderada)}</p><span>Umbral de aprobación: ${r.umbral}%</span></div></div>
  <section class="card" style="margin-top:1rem"><h2>Desglose por área (ponderado)</h2><table><thead><tr><th>Área</th><th class="n">Peso área</th><th class="n">Puntos</th><th style="width:28%">Resultado</th><th class="n">Aporte</th></tr></thead><tbody>
  ${present.map((k) => { const x = r.areas[k], w = areaOf(k).peso || 0; return `<tr><td>${chip(k)}</td><td class="n">${num(w, 0)}%</td><td class="n">${num(x.pts, 0)}/${num(x.max, 0)}</td><td>${bar(x.pct, areaColor(k))}<span class="small muted">${pct(x.pct)} · ${esc(x.nivel)}</span></td><td class="n">${num(w / sumW * x.pct, 1)}</td></tr>`; }).join("")}
  </tbody></table><p class="muted small">Nota ponderada = Σ (peso del área × % obtenido) ÷ Σ pesos de las áreas evaluadas.</p></section>
  <div class="grid g2" style="margin-top:1rem"><section class="card"><h2>Por materia</h2><table><tbody>${Object.values(r.materias).map((x) => `<tr><td>${esc(x.nombre)}</td><td class="n">${x.ok}/${x.n}</td><td class="n"><span class="badge ${x.pct >= r.umbral ? "ok" : "warn"}">${pct(x.pct)}</span></td></tr>`).join("")}</tbody></table></section>
    <section class="card"><h2>Recomendaciones</h2><ul>${r.recomendaciones.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></section></div>
  <section class="card" style="margin-top:1rem"><h2>Retroalimentación de preguntas falladas (${r.fallos.length})</h2>
  ${r.fallos.length ? r.fallos.map((f) => `<div class="fb bad"><b>${esc(f.enunciado)}</b> <span class="badge warn">${f.peso} pt</span><p><b>Tu respuesta:</b> ${f.tu_respuesta ? esc(f.tu_respuesta) : "sin responder"}<br><b>Correcta:</b> ${esc(f.correcta)}<br>${esc(f.retro)}</p></div>`).join("") : `<p class="muted">¡Sin errores!</p>`}</section>`;
}
async function startQuiz(scope, id, n) {
  try { const d = await api("/quiz/start", { scope, id, n: Number(n) || 0 }); await openQuiz(d); } catch (e) { toast(e.message); }
}
async function openQuiz(d) {
  S.report = null;
  S.quiz = { fresh: true, attempt: d.attempt, questions: d.questions, idx: Math.max(0, d.questions.findIndex((x) => x.chosen == null)), sel: null };
  if (d.questions.every((x) => x.chosen != null)) return finishQuiz();
  if (S.view !== "evaluaciones") location.hash = "#evaluaciones"; else render();
}
async function finishQuiz() {
  try { S.report = await api("/quiz/finish", { attempt_id: S.quiz.attempt.id }); S.confetti = !!S.report.attempt.resumen.aprobado; S.quiz = null; await refresh(false); S.attempts = await api("/attempts"); render(); } catch (e) { toast(e.message); }
}

/* ------------------------------------------------------------------ CRONOGRAMA */
async function vCrono() {
  if (!S.sched) S.sched = await api("/schedule");
  const sc = S.sched, cfg = sc.config, today = sc.today;
  const mods = S.boot.modules, sel = cfg.modules && cfg.modules.length ? cfg.modules : mods.map((m) => m.id);
  const items = sc.items;
  const monday = (iso) => { const d = parseD(iso); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.toISOString ? localISO(d) : iso; };
  const cutoff = (() => { const d = parseD(today); d.setDate(d.getDate() - 7); return localISO(d); })();
  const shown = S.showAll ? items : items.filter((i) => i.fecha >= cutoff || i.status === "pending" && i.fecha < today);
  const limit = (() => { const d = parseD(today); d.setDate(d.getDate() + 28); return localISO(d); })();
  const visible = S.showAll ? shown : shown.filter((i) => i.fecha <= limit);
  const weeks = {};
  visible.forEach((i) => { (weeks[monday(i.fecha)] = weeks[monday(i.fecha)] || []).push(i); });
  const wkKeys = Object.keys(weeks).sort();
  const r = sc.resumen;
  const agenda = wkKeys.map((w) => {
    const days = {};
    weeks[w].forEach((i) => (days[i.fecha] = days[i.fecha] || []).push(i));
    const end = parseD(w); end.setDate(end.getDate() + 6);
    const wm = weeks[w].reduce((n, i) => n + i.minutos, 0), wd = weeks[w].filter((i) => i.status === "done").length, wp = Math.round(100 * wd / weeks[w].length);
    return `<div class="week"><h3><span>Semana del ${fmtD(w, { day: "numeric", month: "short" })} al ${fmtD(localISO(end), { day: "numeric", month: "short" })}</span><span class="small muted">${wd}/${weeks[w].length} sesiones · ${fmtMin(wm)}</span></h3>${bar(wp, "var(--ok)")}
    ${Object.keys(days).sort().map((d) => { const dd = parseD(d); return `<div class="day ${d === today ? "today" : ""}"><div class="dn"><span class="dnum">${dd.getDate()}</span><span class="dtxt">${dd.toLocaleDateString("es-CO", { weekday: "short" })}<br>${dd.toLocaleDateString("es-CO", { month: "short" })}</span>${d === today ? '<em class="hoy">Hoy</em>' : ""}</div><div>${days[d].map((it, i) => agendaRow(it, i)).join("")}</div></div>`; }).join("")}</div>`;
  }).join("");
  const dayInputs = DIAS.map((n, i) => `<label>${n}<input type="number" min="0" max="720" step="15" id="cfg-w${i}" value="${cfg.weekly_minutes[String(i)] ?? 0}"></label>`).join("");
  return `<div class="head"><div><h1>Cronograma de estudio</h1><p>Configura tu disponibilidad y genera un calendario según los temas pendientes. Lo que ya completaste se conserva al recalcular.</p></div></div>
  <div class="layout2"><section class="card"><h2>Configuración</h2><div class="cfg">
    <div class="grid g2"><label class="f">Inicio<input type="date" id="cfg-start" value="${cfg.start_date || today}"></label><label class="f">Meta de finalización<input type="date" id="cfg-target" value="${cfg.target_date || ""}"></label></div>
    <div><b class="small">Minutos disponibles por día de la semana</b><div class="wk" style="margin-top:.35rem">${dayInputs}</div></div>
    <div class="grid g2"><label class="f">Profundidad<select id="cfg-depth">${[[0.5, "Repaso rápido (×0,5)"], [0.75, "Ligero (×0,75)"], [1, "Estándar (×1)"], [1.5, "Profundo (×1,5)"], [2, "Intensivo (×2)"]].map(([v, l]) => `<option value="${v}" ${Number(cfg.depth) === v ? "selected" : ""}>${l}</option>`).join("")}</select></label>
      <label class="f">Sesión máxima (min)<select id="cfg-max">${[45, 60, 90, 120, 180].map((v) => `<option ${Number(cfg.max_session) === v ? "selected" : ""}>${v}</option>`).join("")}</select></label></div>
    <label class="f">Orden de materias<select id="cfg-order"><option value="secuencial" ${cfg.order === "secuencial" ? "selected" : ""}>Secuencial (módulo por módulo)</option><option value="intercalado" ${cfg.order === "intercalado" ? "selected" : ""}>Intercalado (alterna áreas)</option></select></label>
    <div><b class="small">Módulos a incluir</b><div class="mods" style="margin-top:.35rem">${mods.map((m) => `<label><input type="checkbox" data-cfgmod="${m.id}" ${sel.includes(m.id) ? "checked" : ""}>${m.orden}. ${esc(m.titulo)}</label>`).join("")}</div></div>
    <label class="row small"><input type="checkbox" id="cfg-eval" ${cfg.include_eval ? "checked" : ""}> Incluir evaluaciones por materia y por módulo</label>
    <div class="row small"><label class="row"><input type="checkbox" id="cfg-review" ${cfg.include_review ? "checked" : ""}> Repaso semanal de flashcards el</label><select id="cfg-rday">${DIAS.map((n, i) => `<option value="${i}" ${Number(cfg.review_day) === i ? "selected" : ""}>${n}</option>`).join("")}</select></div>
    <label class="f">Días bloqueados (vacaciones, exámenes). Uno por línea: <code>2026-12-15..2027-01-10</code><textarea id="cfg-blocked" rows="2">${esc(cfg.blocked || "")}</textarea></label>
    <button class="btn pri" data-act="gen">${items.length ? "Recalcular cronograma" : "Generar cronograma"}</button>
    ${sc.info && sc.info.aviso ? `<div class="banner ${sc.info.fin > (cfg.target_date || "9999") ? "bad" : "ok"}" style="margin:0">${esc(sc.info.aviso)}</div>` : ""}
    <details class="note"><summary>Agregar sesión manual</summary><div class="cfg" style="margin-top:.5rem"><input type="date" id="m-fecha" value="${today}"><input id="m-titulo" placeholder="Ej.: Taller de renta con el grupo"><input type="number" id="m-min" value="60" min="10" step="5"><button class="btn sm" data-act="addmanual">Agregar</button></div></details>
  </div></section>
  <section><div class="grid g3"><div class="card stat"><span>Sesiones completadas</span><b>${r.hechas}/${r.total}</b></div><div class="card stat"><span>Horas pendientes</span><b>${num(r.min_pendientes / 60, 0)}</b></div><div class="card stat"><span>Finalización estimada</span><b style="font-size:1.3rem">${r.fin ? fmtD(r.fin, { day: "numeric", month: "short", year: "numeric" }) : "—"}</b></div></div>
    ${items.length ? `<div class="row" style="margin-top:1rem"><label class="row small"><input type="checkbox" data-chg="showall" ${S.showAll ? "checked" : ""}> Mostrar todo el cronograma (por defecto: próximas 4 semanas)</label></div>${agenda || '<p class="muted">No hay sesiones en este rango.</p>'}` : `<div class="card" style="margin-top:1rem"><p class="muted">Aún no has generado el cronograma. Ajusta tu disponibilidad y presiona «Generar cronograma».</p></div>`}</section></div>`;
}
function localISO(d) { const p = (n) => String(n).padStart(2, "0"); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; }
const agendaRow = (it, i) => sessCard(it, { i, date: true, del: it.origin === "manual" });
function collectCfg() {
  const w = {}; for (let i = 0; i < 7; i++) w[String(i)] = Number($("#cfg-w" + i).value) || 0;
  const mods = [...document.querySelectorAll("[data-cfgmod]")].filter((x) => x.checked).map((x) => x.dataset.cfgmod);
  return { start_date: $("#cfg-start").value, target_date: $("#cfg-target").value, weekly_minutes: w, depth: Number($("#cfg-depth").value), max_session: Number($("#cfg-max").value),
    order: $("#cfg-order").value, modules: mods.length === S.boot.modules.length ? [] : mods, include_eval: $("#cfg-eval").checked, include_review: $("#cfg-review").checked,
    review_day: Number($("#cfg-rday").value), blocked: $("#cfg-blocked").value };
}

/* ------------------------------------------------------------------ AJUSTES */
function vAjustes() {
  const st = S.boot;
  return `<div class="head"><div><h1>Ajustes</h1><p>Pesos de evaluación, umbral de aprobación y copias de seguridad.</p></div></div>
  <div class="grid g2"><section class="card"><h2>Peso de cada área</h2><p class="muted small">Define cuánto pesa cada área en la nota ponderada. No tienen que sumar 100: se normalizan.</p>
    <div class="cfg">${st.areas.map((a) => `<label class="f"><span>${chip(a.id)} ${esc(a.nombre)}</span><input type="number" min="0" max="100" step="1" data-w="${a.id}" value="${a.peso}"></label>`).join("")}
    <label class="f">Umbral de aprobación (%)<input type="number" id="umbral" min="1" max="100" value="${st.settings.umbral}"></label>
    <button class="btn pri" data-act="saveweights">Guardar</button></div></section>
  <section class="card"><h2>Tus datos</h2><p class="muted small">Todo tu progreso vive en el archivo <code>data/progreso.db</code> (SQLite). Además se crea una copia diaria en <code>data/backups/</code>.</p>
    <div class="cfg"><a class="btn" href="/api/backup" download>Descargar copia de seguridad (.db)</a>
    <button class="btn danger" data-act="resetprog">Reiniciar progreso (conserva ajustes)</button><button class="btn danger" data-act="resetall">Reiniciar todo (progreso, notas, pesos)</button></div></section></div>`;
}

/* ------------------------------------------------------------------ eventos */
document.addEventListener("click", async (e) => {
  const t = e.target.closest("[data-act]");
  if (!t) return;
  const act = t.dataset.act, id = t.dataset.id;
  try {
    if (act === "theme") setTheme(t.dataset.v);
    else if (act === "lessondone") { await api("/topic", { subject_id: t.dataset.sid, idx: Number(t.dataset.idx), done: t.dataset.done === "1" }); S.sched = null; await refresh(); toast(t.dataset.done === "1" ? "Tema marcado como estudiado" : "Tema desmarcado"); }
    else if (act === "tupload") await tUpload(id);
    else if (act === "tcopy") {
      const txt = tallerPrompt(S.cur), ta = $("#tprompt");
      ta.value = txt; ta.classList.remove("hidden");
      try { await navigator.clipboard.writeText(txt); toast("Solicitud copiada: pégala en Claude y adjunta tu archivo"); } catch (e) { ta.select(); toast("Selecciona y copia el texto de abajo"); }
    }
    else if (act === "tgrade") { await api("/taller/calificar", { id, nota: Number($("#tnota").value), comentarios: $("#tcom").value }); S.tall = null; toast("Calificación guardada"); render(); }
    else if (act === "treveal") { S.treveal = id; render(); }
    else if (act === "tdel") { if (confirm("¿Eliminar esta entrega?")) { await api("/taller/borrar", { entrega_id: Number(id) }); S.tall = null; render(); } }
    else if (act === "expandall") { S.boot.modules.forEach((m) => S.openMods.add(m.id)); render(); }
    else if (act === "collapseall") { S.openMods.clear(); render(); }
    else if (act === "fcsub") { S.fcSetup = { scope: "subject", id, limit: "0" }; S.fc = null; location.hash = "#flashcards"; render(); }
    else if (act === "studydue") { S.fcSetup = { scope: "due", id: "", limit: "20" }; S.fc = null; }
    else if (act === "quizsub") { S.report = null; S.quiz = null; S.evSetup = { scope: "subject", id, n: "0" }; await startQuiz("subject", id, 0); }
    else if (act === "fcstart") await fcStart();
    else if (act === "fcend") { S.fc = null; await refresh(); }
    else if (act === "flip") doFlip();
    else if (act === "rate") await rate(Number(t.dataset.r));
    else if (act === "fccreate") {
      await api("/flashcards/create", { subject_id: $("#nc-sub").value, front: $("#nc-front").value, back: $("#nc-back").value, nota: $("#nc-nota").value });
      toast("Flashcard guardada"); await loadMyCards(); await refresh();
    } else if (act === "fcdel") { await api("/flashcards/delete", { id }); await loadMyCards(); await refresh(); }
    else if (act === "evstart") { const su = S.evSetup; await startQuiz(su.scope, su.id || (su.scope === "all" ? "" : firstId(su.scope)), su.n); }
    else if (act === "resume") { const d = await api("/quiz/active"); if (d.attempt) await openQuiz(d); }
    else if (act === "discard") { if (confirm("¿Descartar la evaluación en curso? Se perderán sus respuestas.")) { await api("/quiz/discard", { id }); await refresh(); } }
    else if (act === "viewattempt") { S.report = await api("/attempts/" + id); S.quiz = null; if (S.view !== "evaluaciones") location.hash = "#evaluaciones"; else render(); }
    else if (act === "repdone") { S.report = null; render(); }
    else if (act === "opt") { S.quiz.sel = Number(t.dataset.i); render(); }
    else if (act === "confirm") await confirmAnswer();
    else if (act === "next") { const q = S.quiz; q.sel = null; q.fresh = true; if (q.idx + 1 < q.questions.length) { q.idx++; render(); } else await finishQuiz(); }
    else if (act === "evpause") { S.quiz = null; await refresh(); }
    else if (act === "gen") {
      const res = await api("/schedule/generate", { config: collectCfg() }); S.sched = res; await refresh(false); render(); toast("Cronograma actualizado");
    } else if (act === "addmanual") {
      await api("/schedule/add", { fecha: $("#m-fecha").value, titulo: $("#m-titulo").value, minutos: Number($("#m-min").value) }); S.sched = await api("/schedule"); render();
    } else if (act === "delsess") { await api("/schedule/item", { id: Number(id), delete: true }); S.sched = await api("/schedule"); render(); }
    else if (act === "saveweights") {
      const weights = {}; document.querySelectorAll("[data-w]").forEach((i) => (weights[i.dataset.w] = Number(i.value)));
      await api("/areas", { weights }); await api("/settings", { umbral: Number($("#umbral").value) }); await refresh(); toast("Ajustes guardados");
    } else if (act === "resetprog" || act === "resetall") {
      if (confirm(act === "resetall" ? "Se borrará TODO: progreso, notas, flashcards propias y pesos. ¿Continuar?" : "Se borrará tu progreso (temas, flashcards, evaluaciones y cronograma). ¿Continuar?")) {
        await api("/reset", { what: act === "resetall" ? "todo" : "progreso" }); S.sched = null; S.attempts = null; S.fc = null; S.quiz = null; S.report = null; await refresh(); toast("Progreso reiniciado");
      }
    }
  } catch (err) { toast(err.message); }
});
async function confirmAnswer() {
  const q = S.quiz, it = q.questions[q.idx];
  if (q.sel == null || it.chosen != null) return;
  const r = await api("/quiz/answer", { attempt_id: q.attempt.id, pos: it.pos, chosen: q.sel });
  Object.assign(it, { chosen: r.chosen, correct: r.correct, correcta: r.correcta, retro: r.retro, puntos: r.puntos });
  render();
}
document.addEventListener("change", async (e) => {
  const t = e.target, k = t.dataset.chg;
  if (!k) return;
  try {
    if (k === "topic") { await api("/topic", { subject_id: t.dataset.sid, idx: Number(t.dataset.idx), done: t.checked }); S.sched = null; await refresh(); }
    else if (k === "sess") { await api("/schedule/item", { id: Number(t.dataset.id), status: t.checked ? "done" : "pending" }); S.sched = null; await refresh(); }
    else if (k === "movesess") { await api("/schedule/item", { id: Number(t.dataset.id), fecha: t.value }); S.sched = await api("/schedule"); render(); }
    else if (k === "tfilter") { S.tfilter = t.value; render(); }
    else if (k === "showall") { S.showAll = t.checked; render(); }
    else if (k === "fcsetup") { S.fcSetup[t.dataset.k] = t.value; if (t.dataset.k === "scope") S.fcSetup.id = ""; render(); }
    else if (k === "evsetup") { S.evSetup[t.dataset.k] = t.value; if (t.dataset.k === "scope") S.evSetup.id = ""; render(); }
  } catch (err) { toast(err.message); }
});
document.addEventListener("toggle", (e) => {
  const m = e.target.dataset && e.target.dataset.mod;
  if (m) e.target.open ? S.openMods.add(m) : S.openMods.delete(m);
}, true);
let noteTimer;
document.addEventListener("input", (e) => {
  const sid = e.target.dataset && e.target.dataset.note;
  if (!sid) return;
  clearTimeout(noteTimer);
  const val = e.target.value;
  noteTimer = setTimeout(async () => { try { await api("/notes/" + sid, { texto: val }); const s = findSub(sid); if (s) s.nota = val; } catch (err) { toast(err.message); } }, 600);
});
document.addEventListener("keydown", (e) => {
  if (/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
  if (e.target.tagName === "BUTTON" && (e.key === " " || e.key === "Enter")) return;
  if (S.view === "flashcards" && S.fc && S.fc.queue && S.fc.i < S.fc.queue.length) {
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); doFlip(); }
    else if (S.fc.flip && "1234".includes(e.key) && e.key) rate(Number(e.key) - 1);
  } else if (S.view === "evaluaciones" && S.quiz) {
    const it = S.quiz.questions[S.quiz.idx];
    if (it.chosen == null && "1234".includes(e.key) && e.key && Number(e.key) <= it.opciones.length) { S.quiz.sel = Number(e.key) - 1; render(); }
    else if (e.key === "Enter") { e.preventDefault(); it.chosen == null ? confirmAnswer() : document.querySelector('[data-act="next"]')?.click(); }
  }
});
// carga de datos por vista
window.addEventListener("hashchange", async () => {
  if (S.view === "evaluaciones" && !S.attempts) { S.attempts = await api("/attempts"); render(); }
  if (S.view === "flashcards") { await loadMyCards(); render(); }
  if (S.view === "cronograma") { S.sched = await api("/schedule"); render(); }
});
(async function init() {
  try {
    await refresh(false);
    S.attempts = await api("/attempts");
    S.sched = null;
    await loadMyCards();
    render();
  } catch (err) { $("#main").innerHTML = `<p class="pad">No se pudo conectar con el servidor: ${esc(err.message)}</p>`; }
})();
