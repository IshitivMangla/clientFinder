import re
with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'onclick="([^"]+)"', text)
print(set(matches))
