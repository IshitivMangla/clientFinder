import re
with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("IDs in div tags:")
for line in text.split('\n'):
    if 'id=' in line and '<div' in line:
        m = re.search(r'id="([^"]+)"', line)
        if m: print(m.group(1))

print("CSS classes for layout:")
for line in text.split('\n'):
    if 'class="main"' in line or 'class="scroll"' in line:
        print(line.strip())
