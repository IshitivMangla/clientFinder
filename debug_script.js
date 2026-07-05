

window.onerror = function(msg,file,line){
    console.error("JS ERROR:",msg,line);
};

/* ══════════════════════════════════════════
   STATE
══════════════════════════════════════════ */
let leads     = [];
let segStatus = 'all';
let segType   = 'all';
let chartLine = null;
let chartDonut= null;

const TITLES = {leads:'Leads',analytics:'Analytics',controls:'Controls',templates:'Templates',settings:'Settings'};

/* ══════════════════════════════════════════
   INIT & ROUTING
══════════════════════════════════════════ */
function nav(page) {
  document.querySelectorAll('.sb-item').forEach(e => e.classList.remove('active'));
  const link = document.querySelector(`.sb-item[onclick="nav('${page}')"]`);
  if (link) link.classList.add('active');

  document.querySelectorAll('.section, [id^="page-"]').forEach(e => {
    e.style.display = (e.id === 'page-' + page) ? 'block' : 'none';
  });

  const h1 = document.querySelector('.topbar h1');
  if (h1) h1.textContent = TITLES[page] || 'Dashboard';
}

function init() {
  nav('leads');
  fetchStats();
  fetchLeads();
  setInterval(fetchStats, 15000);
  setInterval(fetchLeads, 15000);
}

window.onload = init;

/* ══════════════════════════════════════════
   STATS
══════════════════════════════════════════ */
async function fetchStats() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) { throw Error(res.status); }
    const d = await res.json();
    const s = d.stats || {};
    setText('k-total', s.total_leads ?? '—');
    setText('k-res',   s.restaurant_count ?? '—');
    setText('k-hot',   s.hotel_count ?? '—');
    setText('k-out',   s.outreached ?? '—');
    setText('k-eng',   s.engaged ?? '—');
    setText('k-pend',  s.pending_count ?? '—');
    setText('n-total', (s.restaurant_count||0) + (s.hotel_count||0));
    updateBtns(d.active_tasks || {});
  } catch(err) { console.error('API error', err); }

  try {
    const r2 = await fetch('/api/stats/daily');
    if (!r2.ok) return;
    const d2 = await r2.json();
    const used = d2.api_used_today || 0;
    const el = document.getElementById('api-n');
    if (el) {
      el.textContent = used;
      el.className = used < 180 ? 'g' : used < 240 ? 'a' : 'r';
    }
  } catch(e) {}
}

/* ══════════════════════════════════════════
   LEADS
══════════════════════════════════════════ */
async function fetchLeads() {
  try {
    const res = await fetch(`/api/leads?filter=${segStatus}&type=${segType}`);
    if (!res.ok) { throw Error(res.status); }
    const d = await res.json();
    leads = d.leads || [];
    renderLeads();
  } catch(err) { console.error('API error', err); }
}

function renderLeads() {
  const tbody = document.getElementById('tbody');
  const q = (document.getElementById('search')?.value || '').toLowerCase();

  let rows = leads;
  if (q) rows = rows.filter(l =>
    (l.name    && l.name.toLowerCase().includes(q)) ||
    (l.email   && l.email.toLowerCase().includes(q)) ||
    (l.address && l.address.toLowerCase().includes(q)) ||
    (l.type    && l.type.toLowerCase().includes(q))
  );

  const foot = document.getElementById('tfoot');
  if (foot) foot.textContent = `Showing ${rows.length} lead${rows.length!==1?'s':''} · Auto-refreshes every 15s`;

  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty"><i class="fa-solid fa-box-open"></i><p>No leads match current filters.</p></td></tr>';
    return;
  }

  tbody.innerHTML = rows.map(l => {
    const isHotel = /hotel|lodging|motel|inn/i.test(l.type||'');
    const typeBadge = isHotel
      ? '<span class="badge b-hot"><i class="fa-solid fa-hotel"></i> Hotel</span>'
      : '<span class="badge b-res"><i class="fa-solid fa-utensils"></i> Restaurant</span>';

    const hasWeb = !!(l.website && l.website.trim() && l.website !== 'None');
    const webBadge = hasWeb
      ? '<span class="badge b-hasweb"><i class="fa-solid fa-check"></i> Has Website</span>'
      : '<span class="badge b-noweb"><i class="fa-solid fa-xmark"></i> No Website</span>';

    const STATUS = {
      pending:          ['b-pend',  '⏳ Pending'],
      discovered:       ['b-pend',  '🔍 Discovered'],
      pending_outreach: ['b-ready', '📬 Ready'],
      outreached:       ['b-out',   '📧 Outreached'],
      engaged:          ['b-eng',   '✅ Engaged'],
      no_email_found:   ['b-none',  '❓ No Email'],
      has_website:      ['b-hasweb','🌐 Has Site'],
      skipped_type:     ['b-none',  '— Skipped'],
      skipped_website:  ['b-none',  '— Skipped'],
    };
    const [sc, sl] = STATUS[l.status] || ['b-none', l.status];
    const statusBadge = `<span class="badge ${sc}">${sl}</span>`;

    const emailCell = l.email
      ? `<span style="font-family:monospace;font-size:.74rem;color:var(--t2)">${l.email}</span>`
      : (l.status === 'no_email_found' ? `<span style="color:var(--t3);font-size:.74rem">Not Found</span>` : `<span style="color:var(--t3);font-size:.74rem">Scraping...</span>`);

    const canSend = !!(l.email && l.email.trim());
    const defaultTpl = hasWeb ? 'has_website' : 'no_website';
    const tplSelect = `<select id="tpl-${l.id}" class="btn" style="background:var(--surface2);color:var(--t2);border:1px solid var(--border);padding:6px;border-radius:var(--r-md);margin-right:4px;">
      <option value="no_website" ${defaultTpl === 'no_website' ? 'selected' : ''}>Pitch: No Web</option>
      <option value="has_website" ${defaultTpl === 'has_website' ? 'selected' : ''}>Pitch: Redesign</option>
    </select>`;
    const sendBtn = `<div style="display:flex;align-items:center;">${tplSelect}<button class="btn btn-p" onclick="sendEmail(${l.id},this)" ${canSend?'':'disabled'}>
      <i class="fa-solid fa-paper-plane"></i> Email
    </button></div>`;
    const webBtn = `<button class="btn btn-g" onclick="openSite('${esc(l.website||'')}','${esc(l.name||'')}','${esc(l.address||'')}')">
      <i class="fa-solid fa-${hasWeb?'globe':'magnifying-glass'}"></i> ${hasWeb?'Site':'Search'}
    </button>`;

    return `<tr>
      <td><div class="ln">${l.name||'Unknown'}</div><div class="la"><i class="fa-solid fa-location-dot"></i>${l.address||'—'}</div></td>
      <td>${typeBadge}</td>
      <td>${emailCell}</td>
      <td>${webBadge}</td>
      <td>${statusBadge}</td>
      <td><div class="acts">${sendBtn}${webBtn}</div></td>
    </tr>`;
  }).join('');
}

/* ══════════════════════════════════════════
   SEND EMAIL
══════════════════════════════════════════ */
async function sendEmail(id, btn) {
  const orig = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
  toast('Sending outreach email…', 'info');
  try {
    const res = await fetch(`/api/leads/${id}/send-email`, { method: 'POST' });
    const d = await res.json();
    if (res.ok) {
      toast(d.message || 'Email sent!', 'success');
      clog(d.message || 'Email sent.', 'ok');
      fetchLeads(); fetchStats();
    } else {
      toast(d.detail || 'Failed to send.', 'error');
      btn.disabled = false; btn.innerHTML = orig;
    }
  } catch(e) {
    toast('Network error', 'error');
    btn.disabled = false; btn.innerHTML = orig;
  }
}

function openLeadSite(btn) {
  const lid = parseInt(btn.getAttribute('data-lid'), 10);
  if (isNaN(lid) || !window._siteData) return;
  const l = window._siteData.find(x => x.id === lid);
  if (!l) return;
  openSite(l.website, l.name, l.address);
}

function openSite(url, name, address) {
  if (url && url.trim() && url !== 'None') {
    window.open(/^https?:\/\//i.test(url) ? url : 'http://'+url, '_blank');
  } else {
    window.open('https://www.google.com/search?q='+encodeURIComponent(name+' '+address), '_blank');
  }
}

function openLeadSite(btn) {
  const lid = parseInt(btn.getAttribute('data-lid'), 10);
  if (isNaN(lid) || !window._siteData) return;
  const l = window._siteData.find(x => x.id === lid);
  if (!l) return;
  openSite(l.website, l.name, l.address);
}

/* ══════════════════════════════════════════
   CONTROL BUTTONS
══════════════════════════════════════════ */
function updateBtns(tasks) {
  updBtn('find-leads',    tasks.find_leads,    'Finding Leads…',    'Discover New Leads Now',  'fa-magnifying-glass');
  updBtn('check-replies', tasks.check_replies, 'Checking Replies…', 'Check Email Replies',     'fa-envelope');
  updBtn('outreach',      tasks.outreach,      'Sending Emails…',   'Send Batch Outreach',     'fa-paper-plane');
}

function updBtn(name, running, runLabel, idleLabel, ico) {
  const btn = document.getElementById('btn-'+name); if (!btn) return;
  const span = btn.querySelector('span');
  const icon = btn.querySelector('.ctrl-icon');
  if (running) {
    btn.classList.add('running');
    if (span) span.textContent = runLabel;
    if (icon) icon.className = 'fa-solid fa-spinner ctrl-icon';
  } else {
    btn.classList.remove('running');
    if (span) span.textContent = idleLabel;
    if (icon) icon.className = `fa-solid ${ico} ctrl-icon`;
  }
}

function openLeadSite(btn) {
  const lid = parseInt(btn.getAttribute('data-lid'), 10);
  if (isNaN(lid) || !window._siteData) return;
  const l = window._siteData.find(x => x.id === lid);
  if (!l) return;
  openSite(l.website, l.name, l.address);
}

async function trigger(name) {
  const btn = document.getElementById('btn-'+name);
  if (btn?.classList.contains('running')) return stopTask(name);
  toast(`Starting ${name.replace('-',' ')}…`, 'info');
  try {
    const res = await fetch(`/api/tasks/${name}`, { method: 'POST' });
    const d   = await res.json();
    toast(d.message || d.detail, res.ok ? 'success' : 'error');
    if (res.ok) clog(d.message, 'ok');
  } catch(e) { toast('Network error', 'error'); }
  fetchStats();
}

async function stopTask(name) {
  try {
    const res = await fetch(`/api/tasks/stop/${name}`, { method: 'POST' });
    const d   = await res.json();
    toast(d.message || d.detail, res.ok ? 'warning' : 'error');
  } catch(e) { toast('Network error', 'error'); }
  fetchStats();
}

/* ══════════════════════════════════════════
   ANALYTICS
══════════════════════════════════════════ */
async function loadAnalytics() {
  try {
    const res = await fetch('/api/stats/daily');
    if (!res.ok) { throw Error(res.status); }
    const d = await res.json();

    document.getElementById('a-kpi').innerHTML = `
      <div class="kpi"><div class="kpi-icon" style="background:var(--orange-bg);color:var(--orange)"><i class="fa-solid fa-utensils"></i></div><div class="kpi-label">Restaurants</div><div class="kpi-val">${d.restaurant_count}</div></div>
      <div class="kpi"><div class="kpi-icon" style="background:var(--violet-bg);color:var(--violet)"><i class="fa-solid fa-hotel"></i></div><div class="kpi-label">Hotels</div><div class="kpi-val">${d.hotel_count}</div></div>
      <div class="kpi"><div class="kpi-icon" style="background:var(--sky-bg);color:var(--sky)"><i class="fa-solid fa-paper-plane"></i></div><div class="kpi-label">Outreached</div><div class="kpi-val">${d.outreached_count}</div></div>
      <div class="kpi"><div class="kpi-icon" style="background:var(--amber-bg);color:var(--amber)"><i class="fa-solid fa-clock"></i></div><div class="kpi-label">Pending</div><div class="kpi-val">${d.pending_count}</div></div>
    `;

    const used = d.api_used_today||0;
    const pct  = Math.min(100, Math.round(used/250*100));
    setText('a-api-label', `${used} of 250 API calls used today`);
    setText('a-api-pct',   `${pct}%`);
    const bar = document.getElementById('a-api-bar');
    if (bar) bar.style.width = pct+'%';

    const labels = (d.daily||[]).map(x=>x.day).reverse();
    const counts = (d.daily||[]).map(x=>x.count).reverse();

    if (chartLine) chartLine.destroy();
    const ctx1 = document.getElementById('chart-line')?.getContext('2d');
    if (ctx1) chartLine = new Chart(ctx1, {
      type:'line',
      data:{ labels, datasets:[{ label:'Leads', data:counts,
        borderColor:'#5b5ef4', backgroundColor:'rgba(91,94,244,.08)',
        borderWidth:2, tension:.4, fill:true,
        pointBackgroundColor:'#5b5ef4', pointRadius:3, pointHoverRadius:5
      }]},
      options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false} },
        scales:{
          x:{ ticks:{color:'#475569',font:{size:10,family:'Geist,sans-serif'}}, grid:{color:'rgba(255,255,255,.03)'} },
          y:{ ticks:{color:'#475569',font:{size:10,family:'Geist,sans-serif'}}, grid:{color:'rgba(255,255,255,.03)'}, beginAtZero:true }
        }
      }
    });

    if (chartDonut) chartDonut.destroy();
    const ctx2 = document.getElementById('chart-donut')?.getContext('2d');
    if (ctx2) chartDonut = new Chart(ctx2, {
      type:'doughnut',
      data:{
        labels:['Restaurants','Hotels','Outreached','Pending'],
        datasets:[{
          data:[d.restaurant_count, d.hotel_count, d.outreached_count, d.pending_count],
          backgroundColor:['rgba(251,146,60,.75)','rgba(167,139,250,.75)','rgba(56,189,248,.75)','rgba(245,158,11,.75)'],
          borderWidth:0, hoverOffset:5
        }]
      },
      options:{ responsive:true, maintainAspectRatio:false, cutout:'62%',
        plugins:{ legend:{position:'bottom', labels:{color:'#94a3b8',padding:14,font:{size:11,family:'Geist,sans-serif'}}} }
      }
    });
  } catch(err) { console.error('API error', err); }
}

/* ══════════════════════════════════════════
   TOAST
══════════════════════════════════════════ */
function toast(msg, type='info') {
  const I = {success:'fa-circle-check',error:'fa-circle-xmark',info:'fa-circle-info',warning:'fa-triangle-exclamation'};
  const box = document.getElementById('toast-box');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<i class="fa-solid ${I[type]||'fa-circle-info'}"></i><span>${msg}</span>`;
  box.appendChild(t);
  setTimeout(() => {
    t.style.transition = 'all .35s ease';
    t.style.opacity = '0'; t.style.transform = 'translateX(110%)';
    setTimeout(() => t.remove(), 350);
  }, 4000);
}

/* ══════════════════════════════════════════
   CONSOLE
══════════════════════════════════════════ */
function clog(msg, lvl='i') {
  const con = document.getElementById('console'); if(!con) return;
  const ts = new Date().toLocaleTimeString();
  const cls = {ok:'c-ok',w:'c-w',e:'c-e',i:'c-i'}[lvl]||'c-i';
  const el = document.createElement('div');
  el.className = 'cline';
  el.innerHTML = `<span class="ct">${ts}</span><span class="${cls}">${msg}</span>`;
  con.appendChild(el);
  con.scrollTop = con.scrollHeight;
}

/* ══════════════════════════════════════════
   HELPERS
══════════════════════════════════════════ */
function setText(id, val) { const e=document.getElementById(id); if(e) e.textContent=val; }
function esc(s){ return String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }

// Globals for inline handlers
window.setSeg = function(key, val, btn) {
  if (key === 'status') window.segStatus = val;
  if (key === 'type') window.segType = val;
  if (btn && btn.parentElement) {
    btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }
  if (typeof renderLeads === 'function') renderLeads();
};

window.go = function(page, btn) {
  if (typeof nav === 'function') nav(page);
};

window.login = function() {};
window.refreshData = function() {
    if (typeof fetchStats === 'function') fetchStats();
    if (typeof fetchLeads === 'function') fetchLeads();
};

if (typeof trigger === 'function') window.trigger = trigger;
if (typeof openSite === 'function') window.openSite = openSite;
if (typeof nav === 'function') window.nav = nav;
if (typeof sendEmail === 'function') window.sendEmail = sendEmail;
if (typeof renderLeads === 'function') window.renderLeads = renderLeads;
if (typeof fmtUrl === 'function') window.fmtUrl = fmtUrl;
if (typeof hEsc === 'function') window.hEsc = hEsc;

console.log("Dashboard JS loaded");

