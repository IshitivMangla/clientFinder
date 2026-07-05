import requests, re, urllib.parse
r = requests.get('https://www.google.com/search?q=' + urllib.parse.quote("Mac's Place Charleston email"), headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
print('Status:', r.status_code)
print('Emails:', set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}', r.text)))
