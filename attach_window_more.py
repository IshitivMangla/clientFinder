with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

append_js = '''
if (typeof renderLeads === 'function') window.renderLeads = renderLeads;
if (typeof fmtUrl === 'function') window.fmtUrl = fmtUrl;
if (typeof hEsc === 'function') window.hEsc = hEsc;
'''

text = text.replace('console.log("Dashboard JS loaded");', append_js + '\nconsole.log("Dashboard JS loaded");')

with open('src/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Attached additional functions to window scope')
