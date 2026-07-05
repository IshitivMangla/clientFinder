import re

with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove the local `let segStatus = 'all';` and `let segType = 'all';`
text = re.sub(r'let\s+segStatus\s*=\s*[\'"]all[\'"];', '', text)
text = re.sub(r'let\s+segType\s*=\s*[\'"]all[\'"];', '', text)

# 2. Add window.segStatus and window.segType initialization right after window.onerror
init_globals = '''
window.segStatus = 'all';
window.segType = 'all';
'''
text = text.replace('let leads = [];', init_globals + '\nlet leads = [];')

# 3. Fix fetchLeads to use window.segStatus, window.segType, and a cache buster
fetch_leads_old = 'const res = await fetch(`/api/leads?filter=${segStatus}&type=${segType}`);'
fetch_leads_new = 'const res = await fetch(`/api/leads?filter=${window.segStatus}&type=${window.segType}&_t=${new Date().getTime()}`);'
text = text.replace(fetch_leads_old, fetch_leads_new)

# 4. Make sure setSeg calls fetchLeads instead of renderLeads so the API is hit when filter changes
# Note: In the previous step I used regex to replace renderLeads() with fetchLeads() inside setSeg. 
# Let's ensure it's fully correct.
text = re.sub(r'if \(!res\.ok\) { throw Error\(res\.status\); }', 'if (!res.ok) { throw Error(res.status); }', text) # sanity check

with open('src/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patched dashboard.html successfully.")
