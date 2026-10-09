let trafficChart = null;
let currentWebsiteId = DEFAULT_WEBSITE_ID;

function showToast(msg, duration = 3500) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), duration);
}

function scoreClass(s) {
  if (s >= 80) return "high";
  if (s >= 60) return "mid";
  return "low";
}

function formatNum(n) {
  return Number(n).toLocaleString("en-IN");
}

async function loadAudit(websiteId) {
  currentWebsiteId = websiteId;
  try {
    const res = await fetch(`/api/audit/${websiteId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Failed to load audit");
    }
    const data = await res.json();
    renderAudit(data);
  } catch (e) {
    console.error(e);
    showToast(e.message || "Could not load audit data");
  }
}

function renderAudit(data) {
  const { website, audit, checks, pages, issues, traffic_history } = data;

  // Subtitle
  document.getElementById("auditSubtitle").textContent =
    website.url.replace(/^https?:\/\//, "") + (website.url.endsWith("/") ? "" : "/");

  // Content score
  const cs = audit.content_score;
  document.getElementById("contentScore").textContent = `${cs}/100`;
  document.getElementById("scoreFill").style.width = `${cs}%`;

  // Checks
  const checkList = document.getElementById("checkList");
  checkList.innerHTML = (checks || []).map(c => `
    <li>
      <span class="icon ${c.status}">${c.status === "ok" ? "✓" : "!"}</span>
      <span>${c.label}</span>
      <span class="detail">${c.detail}</span>
    </li>
  `).join("");

  // Readability
  const rs = audit.readability_score;
  document.getElementById("readScore").textContent = rs;
  const badge = document.getElementById("readBadge");
  if (rs >= 70) {
    badge.textContent = "GOOD";
    badge.className = "badge-good";
  } else {
    badge.textContent = "POOR";
    badge.className = "badge-poor";
  }
  const outdated = (issues || [])
    .filter(i => i.type === "low_word_count" || i.type === "missing_meta")
    .reduce((s, i) => s + (i.count || 1), 0);
  document.getElementById("outdatedNote").textContent =
    `${Math.min(outdated, 40)} outdated pages`;

  // Traffic
  document.getElementById("organicTraffic").textContent = formatNum(audit.organic_traffic);

  // Chart
  const labels = (traffic_history || []).map(t => t.month);
  const values = (traffic_history || []).map(t => t.traffic);
  const ctx = document.getElementById("trafficChart").getContext("2d");
  if (trafficChart) trafficChart.destroy();
  trafficChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: values,
        borderColor: "#6c5ce7",
        backgroundColor: "rgba(108,92,231,0.08)",
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { display: true, grid: { display: false }, ticks: { font: { size: 10 }, color: "#8b92a5" } },
        y: { display: false }
      }
    }
  });

  // Issues
  const issuesList = document.getElementById("issuesList");
  issuesList.innerHTML = (issues || []).slice(0, 6).map(i => `
    <li>
      <span class="issue-count">${i.count}</span>
      <span>${i.description}</span>
    </li>
  `).join("") || "<li><span class='muted'>No major issues</span></li>";

  // Pages table
  renderPages(pages || []);
}

function renderPages(pages) {
  const tbody = document.getElementById("pagesTable");
  tbody.innerHTML = pages.map(p => `
    <tr>
      <td>
        <a class="page-title" href="${p.url}" target="_blank" rel="noopener">${p.title || "Untitled"}</a>
        <div class="page-url">${p.url}</div>
      </td>
      <td><span class="score-pill ${scoreClass(p.seo_score)}">${p.seo_score}</span></td>
      <td>${p.readability}</td>
      <td>${Number(p.page_size_kb).toFixed(2)} kb</td>
      <td>${p.load_time_ms} ms</td>
      <td>
        <button class="view-btn" title="View" onclick="window.open('${p.url}','_blank')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        </button>
      </td>
    </tr>
  `).join("") || `<tr><td colspan="6" style="text-align:center;color:#94a3b8;padding:24px;">No pages analyzed yet. Click Run Audit.</td></tr>`;
}

// Table search
document.getElementById("tableSearch").addEventListener("input", function () {
  const q = this.value.toLowerCase();
  document.querySelectorAll("#pagesTable tr").forEach(tr => {
    const text = tr.textContent.toLowerCase();
    tr.style.display = text.includes(q) ? "" : "none";
  });
});

// Website change
document.getElementById("websiteSelect").addEventListener("change", function () {
  loadAudit(parseInt(this.value, 10));
});

// Run Audit
document.getElementById("runAuditBtn").addEventListener("click", async function () {
  const btn = this;
  const websiteId = parseInt(document.getElementById("websiteSelect").value, 10);
  btn.disabled = true;
  btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> Running…`;
  showToast("Audit started… fetching live pages (may take 10–30 sec)");

  try {
    const res = await fetch("/api/run-audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ website_id: websiteId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Audit failed");
    showToast(`Audit completed! Score: ${data.content_score}/100 • ${data.pages_analyzed || 0} pages`);
    await loadAudit(data.website_id);
  } catch (e) {
    console.error(e);
    showToast("Audit failed: " + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3l14 9-14 9V3z"/></svg> Run Audit`;
  }
});

// ---------- Add Website Modal ----------
const modal = document.getElementById("addWebsiteModal");
const addBtn = document.getElementById("addWebsiteBtn");
const cancelBtn = document.getElementById("cancelAddBtn");
const confirmBtn = document.getElementById("confirmAddBtn");
const backdrop = document.getElementById("modalBackdrop");

function openModal() {
  modal.classList.remove("hidden");
  document.getElementById("newWebsiteUrl").value = "";
  document.getElementById("newWebsiteName").value = "";
  document.getElementById("newWebsiteUrl").focus();
}
function closeModal() {
  modal.classList.add("hidden");
}

addBtn.addEventListener("click", openModal);
cancelBtn.addEventListener("click", closeModal);
backdrop.addEventListener("click", closeModal);

confirmBtn.addEventListener("click", async function () {
  const url = document.getElementById("newWebsiteUrl").value.trim();
  const name = document.getElementById("newWebsiteName").value.trim();
  if (!url) {
    showToast("Please enter a website URL");
    return;
  }

  confirmBtn.disabled = true;
  confirmBtn.textContent = "Adding…";

  try {
    // 1. Add website
    const addRes = await fetch("/api/add-website", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, name })
    });
    const addData = await addRes.json();
    if (!addRes.ok) throw new Error(addData.error || "Failed to add website");

    // 2. Refresh select options
    const listRes = await fetch("/api/websites");
    const sites = await listRes.json();
    const select = document.getElementById("websiteSelect");
    select.innerHTML = sites.map(s =>
      `<option value="${s.id}">${s.url}</option>`
    ).join("");
    select.value = addData.id;

    closeModal();
    showToast(addData.already_exists
      ? "Website already exists — running audit…"
      : "Website added — running audit…");

    // 3. Automatically run audit
    const runRes = await fetch("/api/run-audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ website_id: addData.id })
    });
    const runData = await runRes.json();
    if (!runRes.ok) throw new Error(runData.error || "Audit failed");

    showToast(`Done! Score: ${runData.content_score}/100 • ${runData.pages_analyzed || 0} pages`);
    await loadAudit(addData.id);
  } catch (e) {
    console.error(e);
    showToast("Error: " + e.message);
  } finally {
    confirmBtn.disabled = false;
    confirmBtn.textContent = "Add & Audit";
  }
});

// Allow Enter key in modal
document.getElementById("newWebsiteUrl").addEventListener("keydown", (e) => {
  if (e.key === "Enter") confirmBtn.click();
});

// Init
loadAudit(DEFAULT_WEBSITE_ID);
