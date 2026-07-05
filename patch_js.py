import re

with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

append_js = """
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
"""

# Insert before the last </script>
parts = text.rsplit('</script>', 1)
if len(parts) == 2:
    new_text = parts[0] + append_js + '\n</script>' + parts[1]
    with open('src/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Successfully patched JS scope.")
else:
    print("Could not find </script>")
