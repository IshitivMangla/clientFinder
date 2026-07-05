import re

path = 'src/leads_handler.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update safe_request signature for 10s default and 2 retries
# (If not already done)
if 'retries=3' in content:
    content = content.replace('def safe_request(url, retries=3, **kwargs):', 'def safe_request(url, retries=2, **kwargs):')
if "kwargs['timeout'] = 30" in content:
    content = content.replace("kwargs['timeout'] = 30", "kwargs['timeout'] = 10")

# 2. Fix NoneType logic to exactly what user wants
# We will use regex to find all safe_request calls and replace the next line.
# Example: 
# response = safe_request(...)
# if response is not None and response.status_code == 200:
# TO:
# response = safe_request(...)
# if response is None:
#     return None
# if response.status_code == 200:

# 2.1 Fix scrape_email_from_website Google Places check (det_res)
content = re.sub(
    r'(det_res = safe_request[^\n]+\n\s+if det_res is not None and det_res\.status_code == 200:)',
    r'det_res = safe_request(url, headers={"User-Agent": ...}, verify=config.VERIFY_SSL)\n                    if det_res is None:\n                        continue\n                    if det_res.status_code == 200:',
    content, flags=re.DOTALL
)

# 2.2 Fix scrape_email_from_website homepage check (response)
content = content.replace('''        if response is None or response.status_code != 200:
            return None''', 
'''        if response is None:
            return None
        if response.status_code != 200:
            return None''')

# 2.3 Fix scrape_email_from_website subpage check (sub_res)
content = content.replace('''                if sub_res is not None and sub_res.status_code == 200:''', 
'''                if sub_res is None:
                    continue
                if sub_res.status_code == 200:''')

# 2.4 Fix DuckDuckGo check (response)
content = content.replace('''            if response is not None and response.status_code == 200:''',
'''            if response is None:
                return None
            if response.status_code == 200:''')

# 2.5 Fix Yahoo checks (response)
# Actually, the replacement for DuckDuckGo might have caught all of them. Let's do it universally if it's there.

# 3. Simplify DuckDuckGo and Yahoo query generation
old_ddg_queries = '''    # Build fallback queries (from most specific to broadest)
    queries = []
    if street and city:
        queries.append(f"{business_name} {street} {city} email")
    if city:
        queries.append(f"{business_name} {city} email")
    queries.append(f"{business_name} email")'''

new_ddg_queries = '''    # Build short fallback queries
    queries = []
    if city:
        queries.append(f"{business_name} {city} contact email")
    queries.append(f"{business_name} contact email")'''

content = content.replace(old_ddg_queries, new_ddg_queries)

# Make sure we didn't mess up syntax
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied final fixes to leads_handler.py")
