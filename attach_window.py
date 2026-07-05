with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

append_js = '''
if (typeof trigger === 'function') window.trigger = trigger;
if (typeof openSite === 'function') window.openSite = openSite;
if (typeof nav === 'function') window.nav = nav;
if (typeof sendEmail === 'function') window.sendEmail = sendEmail;
'''

text = text.replace('console.log("Dashboard JS loaded");', append_js + '\nconsole.log("Dashboard JS loaded");')

with open('src/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Attached existing functions to window scope')
