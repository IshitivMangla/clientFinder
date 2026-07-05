import re

with open('src/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix body overflow
text = re.sub(r'body\s*\{([^\}]+)overflow:\s*hidden([^\}]*)\}', r'html, body {\1overflow-y:auto\2}', text)

# Add global error logging
error_js = '''
window.onerror = function(msg,file,line){
    console.error("JS ERROR:",msg,line);
};
'''
if 'window.onerror' not in text:
    text = text.replace('<script>', '<script>\n' + error_js)

with open('src/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied fixes to dashboard.html")
