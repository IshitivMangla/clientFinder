import re

path = 'src/leads_handler.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

safe_req_func = '''
import time

def safe_request(url, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 30
            return requests.get(url, **kwargs)
        except Exception as e:
            print(f"Request to {url} failed: {e}. Retrying {attempt+1}/{retries}...")
            time.sleep(5)
    return None
'''

if 'def safe_request' not in content:
    content = content.replace('import requests\n', 'import requests\n' + safe_req_func)

content = content.replace('requests.get(', 'safe_request(')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Refactored leads_handler.py to use safe_request')
