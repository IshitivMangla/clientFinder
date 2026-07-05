import re
with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print('onchange:', set(re.findall(r'onchange="([^"]+)"', text)))
print('onsubmit:', set(re.findall(r'onsubmit="([^"]+)"', text)))
print('oninput:', set(re.findall(r'oninput="([^"]+)"', text)))
print('onkeyup:', set(re.findall(r'onkeyup="([^"]+)"', text)))
