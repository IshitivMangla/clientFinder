import re
with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace /api/stats with /api/status
text = text.replace("const res = await fetch('/api/stats');", "const res = await fetch('/api/status');")

# Replace d.counts with d.stats
text = text.replace("const s = d.counts || {};", "const s = d.stats || {};")

with open('src/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Successfully fixed fetchStats API endpoint in dashboard.html!')
