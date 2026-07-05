import re
with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# find all events
events = re.findall(r'on\w+="([^"]+)"', text)
for ev in set(events):
    print(ev)
