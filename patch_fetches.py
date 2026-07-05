import re

with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace if (!res.ok) return; with if (!res.ok) throw Error(res.status);
text = re.sub(r'if\s*\(!res\.ok\)\s*return;', 'if (!res.ok) { throw Error(res.status); }', text)

# Replace catch(e) { ... } with catch(err) { console.error("API error", err); }
# To be safe, let's just replace the exact lines that I saw
text = text.replace("catch(e) { console.error('stats:', e); }", "catch(err) { console.error('API error', err); }")
text = text.replace("catch(e) { console.error('leads:', e); }", "catch(err) { console.error('API error', err); }")
text = text.replace("catch(e) { console.error(e); }", "catch(err) { console.error('API error', err); }")

with open('src/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patched fetch error handling successfully.")
