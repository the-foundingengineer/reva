// ─── Reva Dashboard — Live Pipeline ───────────────────────────────
const API = window.location.origin + "/api";
const POLL_INTERVAL = 15_000; // 15 seconds

// ── State ───────────────────────────────────────────────────────────
let allLeads = [];
let selectedPhone = null;

// ── Bootstrap ───────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  refreshAll();
  setInterval(refreshAll, POLL_INTERVAL);
});

async function refreshAll() {
  await Promise.all([loadStats(), loadLeads()]);
}

// ── KPI Stats ───────────────────────────────────────────────────────
async function loadStats() {
  try {
    const res = await fetch(`${API}/stats`);
    const d = await res.json();
    el("kpiTotal").textContent     = d.total;
    el("kpiToday").textContent     = d.today;
    el("kpiQualified").textContent = d.qualified;
    el("kpiBooked").textContent    = d.booked;
    el("kpiConversion").textContent = d.conversion_rate + "%";
    if (d.total > 0) {
      el("kpiQualifiedPct").textContent = `${((d.qualified / d.total) * 100).toFixed(1)}% of total`;
    }

    // Funnel bars
    renderFunnel(d);
  } catch (e) {
    console.error("Stats fetch failed:", e);
  }
}

// ── Leads ───────────────────────────────────────────────────────────
async function loadLeads() {
  try {
    const res = await fetch(`${API}/leads`);
    const d = await res.json();
    allLeads = d.leads || [];
    renderPipeline();
    renderActivity();
  } catch (e) {
    console.error("Leads fetch failed:", e);
  }
}

// ── Render Pipeline ─────────────────────────────────────────────────
function renderPipeline() {
  const buckets = { new: [], qualifying: [], qualified: [], booking: [], done: [] };

  allLeads.forEach(lead => {
    const stage = lead.stage || "new";
    if (buckets[stage]) buckets[stage].push(lead);
    else buckets.new.push(lead);
  });

  renderColumn("colNew",        buckets.new,        "countNew");
  renderColumn("colQualifying", buckets.qualifying, "countQualifying");
  renderColumn("colQualified",  buckets.qualified,  "countQualified");
  renderColumn("colBooking",    buckets.booking,    "countBooking");
  renderColumn("colDone",       buckets.done,       "countDone");
}

function renderColumn(containerId, leads, countId) {
  const container = el(containerId);
  el(countId).textContent = leads.length;
  container.innerHTML = "";
  leads.forEach(lead => container.appendChild(createCard(lead)));
}

function createCard(lead) {
  const card = document.createElement("div");
  card.className = "lead-card" + (lead.phone_number === selectedPhone ? " active" : "");
  card.onclick = () => selectLead(lead.phone_number);

  const score = lead.seriousness_score ?? 0;
  const scoreClass = score >= 8 ? "score--high" : score >= 5 ? "score--mid" : "score--low";

  const phone = lead.phone_number || "";
  const masked = phone.length > 6 ? phone.slice(0, 6) + " *** " + phone.slice(-4) : phone;
  const displayName = lead.name || masked.slice(0, 12) + "…";

  // Tags for collected data
  const fields = ["budget", "location", "property_type", "timeline"];
  const tags = fields.map(f => {
    const val = lead[f];
    return `<span class="card__tag ${val ? "card__tag--filled" : ""}">${val || capitalize(f.replace("_", " ")) + " pending"}</span>`;
  }).join("");

  const sourceBadge = lead.source
    ? `<span class="card__source">${esc(formatSource(lead.source))}</span>`
    : "";

  const timeAgo = lead.created_at ? formatTimeAgo(lead.created_at) : "";

  card.innerHTML = `
    <div class="card__top">
      <span class="card__name">${esc(displayName)}</span>
      <span class="card__score ${scoreClass}">${score}/10</span>
    </div>
    <div class="card__phone">${esc(masked)} ${sourceBadge}</div>
    <div class="card__meta">
      ${lead.location ? `<span>${esc(lead.location)}</span>` : ""}
      ${lead.budget ? `· <span>${esc(lead.budget)}</span>` : ""}
      ${lead.property_type ? `· <span>${esc(lead.property_type)}</span>` : ""}
    </div>
    <div class="card__tags">${tags}</div>
    ${timeAgo ? `<div class="card__time">🕐 ${timeAgo}</div>` : ""}
  `;
  return card;
}

// ── Select Lead ─────────────────────────────────────────────────────
async function selectLead(phone) {
  selectedPhone = phone;

  // Highlight active card
  document.querySelectorAll(".lead-card").forEach(c => c.classList.remove("active"));
  document.querySelectorAll(".lead-card").forEach(c => {
    if (c.querySelector(".card__phone")?.textContent.includes(phone.slice(-4))) {
      c.classList.add("active");
    }
  });

  // Show detail panel
  el("detailPlaceholder").classList.add("hidden");
  el("detailContent").classList.remove("hidden");

  try {
    const res = await fetch(`${API}/leads/${phone}`);
    const d = await res.json();
    if (d.error) return;

    const lead = d.lead;
    el("detName").textContent     = lead.name || "—";
    el("detPhone").textContent    = lead.phone_number || "—";
    el("detSource").textContent   = formatSource(lead.source) || "—";
    el("detBudget").textContent   = lead.budget || "—";
    el("detLocation").textContent = lead.location || "—";
    el("detType").textContent     = lead.property_type || "—";
    el("detTimeline").textContent = lead.timeline || "—";
    el("detScore").textContent    = (lead.seriousness_score ?? "—") + "/10";

    renderMatchedUnits(d.matched_units || []);

    // Render conversation
    const thread = el("conversationThread");
    thread.innerHTML = "";
    (d.conversation || []).forEach(msg => {
      const bubble = document.createElement("div");
      bubble.className = `msg msg--${msg.role}`;
      bubble.textContent = msg.message;
      thread.appendChild(bubble);
    });
    thread.scrollTop = thread.scrollHeight;

  } catch (e) {
    console.error("Lead detail fetch failed:", e);
  }
}

// ── Funnel ──────────────────────────────────────────────────────────
function renderFunnel(stats) {
  const total = stats.total || 1;
  const stages = [
    { key: "new",        label: "New",        val: stats.new,        cls: "funnel-fill--new" },
    { key: "qualifying", label: "Qualifying", val: stats.qualifying, cls: "funnel-fill--qualifying" },
    { key: "qualified",  label: "Qualified",  val: stats.qualified,  cls: "funnel-fill--qualified" },
    { key: "booked",     label: "Booked",     val: stats.booked,     cls: "funnel-fill--booked" },
  ];

  const container = el("funnelBars");
  container.innerHTML = stages.map(s => {
    const pct = Math.max(((s.val / total) * 100), 2);
    return `
      <div class="funnel-row">
        <span class="funnel-label">${s.label}</span>
        <div class="funnel-track">
          <div class="funnel-fill ${s.cls}" style="width:${pct}%"></div>
        </div>
        <span class="funnel-label" style="width:30px;text-align:left">${s.val}</span>
      </div>
    `;
  }).join("");
}

// ── Activity Feed ───────────────────────────────────────────────────
function renderActivity() {
  const feed = el("activityFeed");
  if (!allLeads.length) {
    feed.innerHTML = '<div class="activity-placeholder">No activity yet</div>';
    return;
  }

  // Show most recent leads as activity items
  const recent = allLeads.slice(0, 8);
  feed.innerHTML = recent.map(lead => {
    const iconClass = lead.stage === "done" ? "activity-icon--booked"
                    : lead.stage === "qualified" ? "activity-icon--qualified"
                    : "activity-icon--msg";
    const emoji = lead.stage === "done" ? "📅"
                : lead.stage === "qualified" ? "✅"
                : "💬";
    const phone = lead.phone_number || "";
    const name = lead.name || phone.slice(0, 8) + "…";
    const action = lead.stage === "done" ? "booked a meeting"
                 : lead.stage === "qualified" ? "fully qualified"
                 : lead.stage === "qualifying" ? "in conversation"
                 : "just messaged";
    const time = lead.created_at ? formatTimeAgo(lead.created_at) : "";

    return `
      <div class="activity-item">
        <div class="activity-icon ${iconClass}">${emoji}</div>
        <div class="activity-body"><strong>${esc(name)}</strong> ${action}${time ? " · " + time : ""}</div>
      </div>
    `;
  }).join("");
}

// ── Utilities ───────────────────────────────────────────────────────
function el(id) { return document.getElementById(id); }

function esc(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function formatSource(source) {
  if (!source) return "";
  return source.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function formatPriceNaira(n) {
  if (!n) return "—";
  if (n >= 1_000_000) {
    const m = n / 1_000_000;
    return m % 1 === 0 ? `₦${m}M` : `₦${m.toFixed(1)}M`;
  }
  return `₦${n.toLocaleString()}`;
}

function renderMatchedUnits(matches) {
  const container = el("matchedUnits");
  if (!matches.length) {
    container.innerHTML = '<p class="matched-units__empty">No units offered yet</p>';
    return;
  }

  container.innerHTML = matches.map(m => {
    const u = m.units || m;
    const dev = u.developments || {
      name: u.development_name || m.development_name || "",
      location: u.location || m.location || "",
    };
    const price = formatPriceNaira(u.price_naira ?? m.price_naira);
    const rank = m.rank ? `#${m.rank} ` : "";
    return `
      <div class="matched-unit-card">
        <div class="matched-unit-card__title">${rank}${esc(u.title || u.unit_code || "Unit")}</div>
        <div class="matched-unit-card__meta">${esc(dev.name || "")} · ${esc(dev.location || "")}</div>
        <div class="matched-unit-card__price">${esc(price)}${m.match_score ? ` · match ${Math.round(m.match_score)}%` : ""}</div>
      </div>
    `;
  }).join("");
}

function formatTimeAgo(isoStr) {
  try {
    const d = new Date(isoStr);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60)   return "just now";
    if (diff < 3600) return Math.floor(diff / 60) + " min ago";
    if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
    return Math.floor(diff / 86400) + "d ago";
  } catch { return ""; }
}
