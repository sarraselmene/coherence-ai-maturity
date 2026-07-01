/* =========================================================================
   MaturAI — SPA d'évaluation de la maturité IA (vanilla JS, zéro dépendance)
   Flux : landing → contexte → 5 axes (QCM) → ROI → résultats (radar, scores,
   incohérences, ROI, recommandations). Aligné sur la charte KPMG.
   ========================================================================= */
"use strict";

const AXIS_COLORS = {
  strategy: "#1e49e2", data: "#00b8f5", talents: "#7213ea",
  technology: "#00338d", governance: "#fd349c",
};

const state = {
  ref: null,
  steps: [],
  idx: 0,
  answers: {},     // {questionId: score}
  context: {},     // {region, headcount, revenue, role, department}
  sector: null,
  roi: {},         // {field: value}
  result: null,
};

const $ = (sel) => document.querySelector(sel);

/* ----------------------------- Initialisation --------------------------- */
async function init() {
  try {
    const res = await fetch("/api/referential");
    state.ref = await res.json();
  } catch (e) {
    $("#screen").innerHTML = `<div class="card"><h2>Erreur</h2><p>Impossible de charger le référentiel. Le serveur est-il lancé ?</p></div>`;
    return;
  }
  buildSteps();
  render();
}

function buildSteps() {
  state.steps = [{ type: "landing", label: "Accueil" }, { type: "context", label: "Contexte" }];
  state.ref.axes.forEach((ax) => state.steps.push({ type: "axis", label: ax.name, axis: ax }));
  state.steps.push({ type: "roi", label: "ROI" });
  state.steps.push({ type: "results", label: "Résultats" });
}

/* ------------------------------- En-tête -------------------------------- */
function renderStepper() {
  const items = state.steps.filter((s) => s.type !== "landing");
  const cur = state.steps[state.idx];
  $("#steps").innerHTML = items
    .map((s) => {
      const curIndex = state.steps.indexOf(cur);
      const sIndex = state.steps.indexOf(s);
      let cls = "steps__item";
      if (s === cur) cls += " is-active";
      else if (sIndex < curIndex) cls += " is-done";
      const short = s.type === "axis" ? s.axis.name.split(" ")[0] : s.label;
      return `<span class="${cls}">${short}</span>`;
    })
    .join("");
  const pct = (state.idx / (state.steps.length - 1)) * 100;
  $("#progressBar").style.width = `${pct}%`;
}

/* ------------------------------- Rendu ---------------------------------- */
function render() {
  renderStepper();
  const step = state.steps[state.idx];
  const screen = $("#screen");
  if (step.type === "landing") screen.innerHTML = viewLanding();
  else if (step.type === "context") screen.innerHTML = viewContext();
  else if (step.type === "axis") screen.innerHTML = viewAxis(step.axis);
  else if (step.type === "roi") screen.innerHTML = viewRoi();
  else if (step.type === "results") { screen.innerHTML = viewResultsLoading(); runAssessment(); }
  window.scrollTo({ top: 0, behavior: "smooth" });
  bindScreen();
}

function navButtons(nextLabel = "Suivant", nextEnabled = true) {
  const back = state.idx > 1 ? `<button class="btn btn--outline" data-act="prev">← Précédent</button>` : `<span></span>`;
  const next = `<button class="btn btn--cobalt" data-act="next" ${nextEnabled ? "" : "disabled"}>${nextLabel}</button>`;
  return `<div class="nav">${back}${next}</div>`;
}

/* ------------------------------- Landing -------------------------------- */
function viewLanding() {
  const motif = `<svg class="hero__motif" width="220" height="220" viewBox="0 0 220 220" fill="none">
    ${[0,1,2,3].map(i=>`<rect x="${20+i*30}" y="${10+i*18}" width="46" height="46" rx="6" fill="rgba(255,255,255,${0.10+i*0.06})"/>`).join("")}
  </svg>`;
  return `
  <section class="hero">
    ${motif}
    <h1>Évaluez la maturité IA de votre organisation</h1>
    <p>Un diagnostic structuré sur 5 dimensions, fondé sur des référentiels reconnus
       (PwC, DAMA-DMBOK, ISO/IEC 42001, NIST AI RMF, EU AI Act) et un moteur de
       <strong>logique floue</strong> qui nuance le score et détecte les incohérences.</p>
    <div class="hero__facts">
      <div class="fact"><b>33</b><span>questions traçables</span></div>
      <div class="fact"><b>5</b><span>dimensions clés</span></div>
      <div class="fact"><b>1–5</b><span>niveau de maturité (CMMI)</span></div>
      <div class="fact"><b>ROI</b><span>impact financier estimé</span></div>
    </div>
    <div class="hero__cta">
      <button class="btn btn--primary" data-act="next">Démarrer l'évaluation</button>
    </div>
  </section>
  <div class="card" style="margin-top:18px">
    <h3>Les 5 dimensions évaluées</h3>
    <div class="kpi-row" style="grid-template-columns:repeat(5,1fr)">
      ${state.ref.axes.map(ax=>`<div class="kpi"><b style="color:${AXIS_COLORS[ax.id]}">${ax.name.split(" ")[0]}</b><span>${(ax.anchor||[]).join(", ")}</span></div>`).join("")}
    </div>
  </div>`;
}

/* ------------------------------- Contexte ------------------------------- */
function selectField(id, field, label, options, value) {
  const opts = ['<option value="">— Sélectionner —</option>']
    .concat(options.map((o) => `<option value="${o}" ${o===value?"selected":""}>${o}</option>`))
    .join("");
  return `<div class="field"><label>${label}</label><select class="js-ctx" data-field="${field}">${opts}</select></div>`;
}

function viewContext() {
  const cq = state.ref.context_questions;
  const find = (f) => cq.find((q) => q.field === f) || { options: [] };
  return `
  <div class="card">
    <h2>Contexte de l'organisation</h2>
    <p class="muted">Ces informations contextualisent le rapport et n'entrent pas dans le score de maturité.</p>
    <div class="grid-2">
      ${selectField("sector","sector","Secteur d'activité", state.ref.sectors, state.sector)}
      ${selectField("region","region","Région", find("region").options, state.context.region)}
      ${selectField("headcount","headcount","Effectif total", find("headcount").options, state.context.headcount)}
      ${selectField("revenue","revenue","Chiffre d'affaires annuel", find("revenue").options, state.context.revenue)}
      ${selectField("role","role","Votre rôle", find("role").options, state.context.role)}
      ${selectField("department","department","Votre département", find("department").options, state.context.department)}
    </div>
  </div>
  ${navButtons("Commencer le questionnaire")}`;
}

/* -------------------------------- Axe ----------------------------------- */
function viewAxis(ax) {
  const axisNum = state.ref.axes.indexOf(ax) + 1;
  const answered = ax.subdomains.flatMap((s) => s.questions).filter((q) => state.answers[q.id] !== undefined).length;
  const total = ax.subdomains.flatMap((s) => s.questions).length;
  let html = `
  <div class="card">
    <div class="axis-head">
      <div class="axis-head__num" style="background:${AXIS_COLORS[ax.id]}">${axisNum}</div>
      <div>
        <h2>${ax.name}</h2>
        <div class="axis-head__anchor">Référentiel : ${(ax.anchor||[]).map(a=>state.ref.meta.sources[a]||a).join(" · ")}</div>
      </div>
      <div style="margin-left:auto" class="muted">${answered}/${total} répondu(s)</div>
    </div>`;
  ax.subdomains.forEach((sd) => {
    html += `<div class="subdomain"><div class="subdomain__title">${sd.id} — ${sd.name}</div>`;
    sd.questions.forEach((q) => { html += questionBlock(q); });
    html += `</div>`;
  });
  html += `</div>` + navButtons("Suivant");
  return html;
}

function questionBlock(q) {
  const layerBadge = q.layer === "ai_specific"
    ? `<span class="badge badge--ai">Couche IA-spécifique</span>`
    : `<span class="badge badge--gen">Référentiel générique</span>`;
  const srcBadges = q.sources.map((s) => `<span class="badge badge--src">${state.ref.meta.sources[s] || s}</span>`).join("");
  const opts = q.levels.map((lvl) => {
    const sel = state.answers[q.id] === lvl.score ? "is-selected" : "";
    return `<div class="option ${sel}" data-qid="${q.id}" data-score="${lvl.score}">
      <span class="option__dot"></span>
      <span><span class="option__score">${lvl.score}</span> ${lvl.label}</span>
    </div>`;
  }).join("");
  return `
  <div class="question">
    <div class="question__text"><span class="qid">${q.id}</span><span>${q.text}</span></div>
    <div class="badges">${layerBadge}${srcBadges}</div>
    <div class="options">${opts}</div>
  </div>`;
}

/* -------------------------------- ROI ----------------------------------- */
function viewRoi() {
  const num = (f, label, unit) => `
    <div class="field"><label>${label} ${unit?`<small>(${unit})</small>`:""}</label>
    <input class="input js-roi" type="number" min="0" data-field="${f}" value="${state.roi[f] ?? ""}" placeholder="0"></div>`;
  const sel = (f, label, options) => {
    const opts = ['<option value="">— Sélectionner —</option>'].concat(options.map(o=>`<option ${state.roi[f]===o?"selected":""}>${o}</option>`)).join("");
    return `<div class="field"><label>${label}</label><select class="js-roi" data-field="${f}">${opts}</select></div>`;
  };
  return `
  <div class="card">
    <h2>Impact financier (ROI / ETP)</h2>
    <p class="muted">Données factuelles servant au calcul Monte Carlo, pondéré par votre maturité. Optionnel — laissez vide pour ignorer le ROI.</p>
    <div class="grid-2">
      ${num("n_automatable_tasks","Tâches automatisables identifiées","nombre")}
      ${num("hours_per_week","Temps hebdomadaire sur ces tâches","heures/sem.")}
      ${num("cost_per_fte","Coût chargé d'un ETP","€/an")}
      ${num("ai_budget","Budget IA annuel","€/an")}
      ${sel("measured_gains","Gains de productivité déjà mesurés ?",["Oui avec métriques","Estimés","Non mesurés"])}
      ${sel("risk_cost","Coût du risque IA estimé ?",["Oui chiffré","Estimation grossière","Non"])}
    </div>
  </div>
  ${navButtons("Voir mes résultats")}`;
}

/* ------------------------------ Résultats ------------------------------- */
function viewResultsLoading() {
  return `<div class="card center"><div class="spinner"></div><p class="muted">Calcul du score flou, de l'incertitude et du ROI…</p></div>`;
}

async function runAssessment() {
  const payload = {
    client_name: "Organisation évaluée",
    sector: state.sector,
    context: state.context,
    answers: state.answers,
    roi_inputs: state.roi,
  };
  try {
    const res = await fetch("/api/assess", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text());
    state.result = await res.json();
    $("#screen").innerHTML = viewResults(state.result);
    bindScreen();
  } catch (e) {
    $("#screen").innerHTML = `<div class="card"><h2>Erreur de calcul</h2><pre class="muted">${String(e).slice(0,400)}</pre>${navButtons("",false)}</div>`;
    bindScreen();
  }
}

function viewResults(result) {
  const s = result.score;
  const g = s.global;
  const axes = s.axes.map((a) => ({ id: a.axis_id, label: a.name, value: a.presented_level, crisp: a.crisp, unc: a.uncertainty }));
  const radar = radarSVG(axes);

  const axisBars = s.axes
    .slice().sort((a,b)=>b.crisp-a.crisp)
    .map((a) => `
      <div class="axis-bar">
        <div>${a.name}</div>
        <div class="axis-bar__track"><div class="axis-bar__fill" style="width:${(a.crisp/4)*100}%;background:${AXIS_COLORS[a.axis_id]}"></div></div>
        <div class="axis-bar__val">${a.presented_level.toFixed(1)}</div>
      </div>`).join("");

  const incoh = (s.incoherences || []).length
    ? s.incoherences.map((r) => `
        <div class="alert">
          <div class="alert__title">${r.name.replace(/_/g," ")}<span class="tag-sev">${sevLabel(r.severity)}</span></div>
          <div>${r.description}</div>
          <div class="muted">Axes concernés : ${r.axes_involved.join(", ")} · intensité ${r.strength.toFixed(2)}</div>
        </div>`).join("")
    : `<p class="muted">Aucune incohérence inter-axes significative détectée.</p>`;

  const roi = result.roi ? roiCards(result.roi) : `<p class="muted">ROI non calculé (renseignez budget et heures à l'étape ROI).</p>`;

  return `
  <div class="result-grid">
    <div class="card gauge">
      <div class="gauge__sub">Niveau de maturité IA global</div>
      <div class="gauge__value">${g.presented_level.toFixed(1)}<span style="font-size:24px;color:var(--grey-400)"> / 5</span></div>
      <div class="gauge__band">Intervalle de crédibilité : ${(g.credibility_interval[0]+1).toFixed(1)} – ${(g.credibility_interval[1]+1).toFixed(1)}</div>
      <hr style="border:none;border-top:1px solid var(--grey-200);margin:16px 0">
      <div class="compare">
        <div class="compare__item"><b style="color:var(--kpmg-blue)">${(g.presented_level).toFixed(1)}</b><div class="muted">moteur flou</div></div>
        <div class="compare__sep">vs</div>
        <div class="compare__item"><b style="color:var(--grey-400)">${(g.classic_weighted_mean+1).toFixed(1)}</b><div class="muted">moyenne classique</div></div>
      </div>
      <p class="muted" style="margin-top:8px">Écart net du moteur flou : <b>${g.fuzzy_vs_classic_gap.toFixed(2)}</b> (dont pénalité d'incohérence ${g.incoherence_penalty.toFixed(2)}).</p>
    </div>
    <div class="card">
      <h3>Profil par dimension</h3>
      ${radar}
    </div>
  </div>

  <div class="card">
    <h3>Scores par axe</h3>
    ${axisBars}
  </div>

  <div class="card">
    <h3>Incohérences &amp; risques détectés</h3>
    ${incoh}
  </div>

  <div class="card">
    <h3>Impact financier (ROI Monte Carlo)</h3>
    ${roi}
  </div>

  <div class="card">
    <h3>Synthèse &amp; recommandations</h3>
    <div class="report">${mdToHtml(result.report_markdown)}</div>
    <div class="nav">
      <button class="btn btn--outline" data-act="download">⬇ Télécharger le rapport (.md)</button>
      <button class="btn btn--cobalt" data-act="restart">Nouvelle évaluation</button>
    </div>
  </div>`;
}

function roiCards(roi) {
  return `
  <div class="kpi-row">
    <div class="kpi"><b>${roi.fte_saved.median.toFixed(1)}</b><span>ETP économisables (médian)<br>P10 ${roi.fte_saved.p10.toFixed(1)} – P90 ${roi.fte_saved.p90.toFixed(1)}</span></div>
    <div class="kpi"><b>${fmtEur(roi.annual_savings_eur.median)}</b><span>gains annuels (médian)</span></div>
    <div class="kpi"><b>${Math.round(roi.prob_roi_positive*100)}%</b><span>probabilité ROI &gt; 0</span></div>
  </div>
  <p class="muted" style="margin-top:10px">ROI médian : <b>${roi.roi_ratio.median.toFixed(2)}</b> · ${roi.n_simulations.toLocaleString("fr-FR")} simulations Monte Carlo.</p>`;
}

/* ----------------------------- Radar SVG -------------------------------- */
function radarSVG(axes) {
  const W = 460, H = 360, cx = W/2, cy = H/2 + 6, R = 130, max = 5, n = axes.length;
  const ang = (i) => -Math.PI/2 + (i*2*Math.PI)/n;
  const pt = (i, r) => [cx + r*Math.cos(ang(i)), cy + r*Math.sin(ang(i))];

  let grid = "";
  for (let lvl = 1; lvl <= max; lvl++) {
    const r = (R*lvl)/max;
    const poly = axes.map((_, i) => pt(i, r).join(",")).join(" ");
    grid += `<polygon points="${poly}" fill="none" stroke="#dfe4ec" stroke-width="1"/>`;
  }
  let spokes = "", labels = "";
  axes.forEach((a, i) => {
    const [x, y] = pt(i, R);
    spokes += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#dfe4ec" stroke-width="1"/>`;
    const [lx, ly] = pt(i, R + 26);
    const anchor = Math.abs(lx-cx) < 8 ? "middle" : (lx > cx ? "start" : "end");
    labels += `<text x="${lx}" y="${ly}" text-anchor="${anchor}" font-size="12" font-weight="700" fill="#0c233c">${a.label.split(" ")[0]}</text>
               <text x="${lx}" y="${ly+14}" text-anchor="${anchor}" font-size="11" fill="#5b6878">${a.value.toFixed(1)}/5</text>`;
  });
  const valPoly = axes.map((a, i) => pt(i, (R*a.value)/max).join(",")).join(" ");
  const dots = axes.map((a, i) => { const [x,y]=pt(i,(R*a.value)/max); return `<circle cx="${x}" cy="${y}" r="4" fill="${AXIS_COLORS[a.id]||"#1e49e2"}"/>`; }).join("");

  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Radar des scores par axe">
    ${grid}${spokes}
    <polygon points="${valPoly}" fill="rgba(30,73,226,.18)" stroke="#1e49e2" stroke-width="2"/>
    ${dots}${labels}
  </svg>`;
}

/* --------------------------- Mini markdown ------------------------------ */
function mdToHtml(md) {
  const esc = (t) => t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  const inline = (t) => esc(t).replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/\*(.+?)\*/g,"<em>$1</em>");
  const lines = md.split("\n");
  let html = "", i = 0, inList = false, inTable = false;
  const closeList = () => { if (inList) { html += "</ul>"; inList = false; } };
  const closeTable = () => { if (inTable) { html += "</tbody></table>"; inTable = false; } };
  while (i < lines.length) {
    let line = lines[i];
    if (/^\s*\|/.test(line) && /\|/.test(line)) {
      const cells = line.split("|").slice(1,-1).map((c)=>c.trim());
      if (/^[-:\s|]+$/.test(line.replace(/\|/g,"-"))) { i++; continue; } // séparateur
      if (!inTable) { closeList(); html += '<table><tbody>'; inTable = true; }
      const isHeader = !/\d/.test(cells.join("")) && cells.every((c)=>c.length<40) && (i+1<lines.length && /^[\s|:-]+$/.test(lines[i+1]));
      const tag = isHeader ? "th" : "td";
      html += "<tr>" + cells.map((c)=>`<${tag}>${inline(c)}</${tag}>`).join("") + "</tr>";
      i++; continue;
    } else closeTable();

    if (/^### /.test(line)) { closeList(); html += `<h3>${inline(line.slice(4))}</h3>`; }
    else if (/^## /.test(line)) { closeList(); html += `<h2>${inline(line.slice(3))}</h2>`; }
    else if (/^# /.test(line)) { closeList(); html += `<h1>${inline(line.slice(2))}</h1>`; }
    else if (/^---\s*$/.test(line)) { closeList(); html += "<hr>"; }
    else if (/^\s*-\s+/.test(line)) { if (!inList) { html += "<ul>"; inList = true; } html += `<li>${inline(line.replace(/^\s*-\s+/,""))}</li>`; }
    else if (line.trim() === "") { closeList(); }
    else { closeList(); html += `<p>${inline(line)}</p>`; }
    i++;
  }
  closeList(); closeTable();
  return html;
}

/* ---------------------------- Interactions ------------------------------ */
function bindScreen() {
  const screen = $("#screen");
  screen.querySelectorAll(".option").forEach((el) => {
    el.addEventListener("click", () => {
      const qid = el.dataset.qid, score = Number(el.dataset.score);
      state.answers[qid] = score;
      el.parentElement.querySelectorAll(".option").forEach((o) => o.classList.remove("is-selected"));
      el.classList.add("is-selected");
      const head = screen.querySelector(".axis-head__anchor");
      // met à jour le compteur "répondu"
      const counter = screen.querySelector(".axis-head .muted");
      if (counter) {
        const ax = state.steps[state.idx].axis;
        const total = ax.subdomains.flatMap((s)=>s.questions).length;
        const answered = ax.subdomains.flatMap((s)=>s.questions).filter((q)=>state.answers[q.id]!==undefined).length;
        counter.textContent = `${answered}/${total} répondu(s)`;
      }
    });
  });
  screen.querySelectorAll(".js-ctx").forEach((el) => {
    el.addEventListener("change", () => {
      const f = el.dataset.field;
      if (f === "sector") state.sector = el.value || null;
      else state.context[f] = el.value;
    });
  });
  screen.querySelectorAll(".js-roi").forEach((el) => {
    el.addEventListener("change", () => {
      const v = el.value;
      state.roi[el.dataset.field] = el.type === "number" ? (v === "" ? undefined : Number(v)) : v;
    });
  });
  screen.querySelectorAll("[data-act]").forEach((el) => {
    el.addEventListener("click", () => handleAction(el.dataset.act));
  });
}

function handleAction(act) {
  if (act === "next") { if (state.idx < state.steps.length - 1) { state.idx++; render(); } }
  else if (act === "prev") { if (state.idx > 0) { state.idx--; render(); } }
  else if (act === "restart") { state.idx = 0; state.answers = {}; state.context = {}; state.roi = {}; state.sector = null; state.result = null; render(); }
  else if (act === "download") downloadReport();
}

function downloadReport() {
  if (!state.result) return;
  const blob = new Blob([state.result.report_markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "rapport_maturite_ia.md"; a.click();
  URL.revokeObjectURL(url);
}

/* ------------------------------- Utils ---------------------------------- */
function sevLabel(s) { return { SMALL: "faible", MEDIUM: "modérée", LARGE: "élevée" }[s] || s; }
function fmtEur(v) { return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(v); }

init();
