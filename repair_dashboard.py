import re
with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if '/* ════════════════════════════════════' in line and '// Store site data' in line:
        start_idx = i
    if 'STATS' in line and '══════════════════════════════════════════ */' in lines[i-1]:
        end_idx = i - 2 # go above the STATS header

if end_idx == -1:
    # If the exact match fails, let's search for "STATS"
    for i, line in enumerate(lines):
        if 'STATS' in line and '═════' in lines[i-1]:
            end_idx = i - 2
            break

if start_idx != -1 and end_idx != -1:
    new_block = '''/* ══════════════════════════════════════════
   INIT & ROUTING
══════════════════════════════════════════ */
function nav(page) {
  document.querySelectorAll('.sb-item').forEach(e => e.classList.remove('active'));
  const link = document.querySelector(`.sb-item[onclick="nav('${page}')"]`);
  if (link) link.classList.add('active');

  document.querySelectorAll('.section').forEach(e => {
    e.style.display = (e.id === 'sec-' + page) ? 'block' : 'none';
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
'''
    new_lines = lines[:start_idx] + new_block.split('\n') + lines[end_idx+1:]
    with open('src/dashboard.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print('Successfully repaired init and routing!')
else:
    print(f'Could not find the target block! {start_idx} {end_idx}')
