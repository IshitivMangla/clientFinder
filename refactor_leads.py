import re

path = 'src/leads_handler.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update safe_request signature for 10s default and 2 retries
content = content.replace('def safe_request(url, retries=3, **kwargs):', 'def safe_request(url, retries=2, **kwargs):')
content = content.replace("kwargs['timeout'] = 30", "kwargs['timeout'] = 10")

# 2. Fix NoneType bugs. We will find `if .*status_code` right after safe_request and insert a None check.
content = re.sub(r'(response = safe_request\([^\)]+\)\s+)(if response\.status_code)', r'\1if response is None or response.status_code', content)
content = re.sub(r'(det_res = safe_request\([^\)]+\)\s+)(if det_res\.status_code)', r'\1if det_res is None or det_res.status_code', content)
content = re.sub(r'(sub_res = safe_request\([^\)]+\)\s+)(if sub_res\.status_code)', r'\1if sub_res is None or sub_res.status_code', content)

# 3. Add clean_business_name function and apply it to DuckDuckGo search
clean_func = '''
def clean_business_name(name):
    """Strip legal entities, brand names, and special chars for better search results."""
    # Remove by Wyndham, by IHG, Tribute Portfolio, LLC, Inc
    cleaned = re.sub(r'(?i)\\b(?:by Wyndham|by IHG|Tribute Portfolio|LLC|Inc)\\b', '', name)
    # Remove commas, hyphens, special chars
    cleaned = re.sub(r'[^a-zA-Z0-9\\s]', ' ', cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r'\\s+', ' ', cleaned).strip()
    return cleaned
'''
if 'def clean_business_name' not in content:
    content = content.replace('def get_us_locations():', clean_func + '\ndef get_us_locations():')

# Apply it in search_duckduckgo_for_email
content = content.replace('def search_duckduckgo_for_email(business_name, address):', 'def search_duckduckgo_for_email(business_name, address):\n    business_name = clean_business_name(business_name)')

# Do the same for yahoo if it exists
if 'def search_yahoo_for_email(business_name, address):' in content:
    content = content.replace('def search_yahoo_for_email(business_name, address):', 'def search_yahoo_for_email(business_name, address):\n    business_name = clean_business_name(business_name)')

# 4. Enhance scrape_email_from_website to explicitly try the hardcoded paths
# Replace the network path logic with the explicit paths the user asked for
old_scrape = '''        # 3. Network path analysis - look for contact/about pages
        links_to_crawl = []
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            if 'contact' in href or 'about' in href or 'reach' in href or 'support' in href:
                full_link = urllib.parse.urljoin(url, a['href'])
                if full_link not in links_to_crawl and full_link.startswith('http'):
                    links_to_crawl.append(full_link)
                    
        # Crawl up to 3 relevant sub-pages
        for sub_url in links_to_crawl[:3]:'''

new_scrape = '''        # 3. Explicitly scrape hardcoded contact paths as requested
        paths = ['/contact', '/contact-us', '/about', '/team']
        base_url = url.rstrip('/')
        links_to_crawl = [base_url + p for p in paths]
        
        # Crawl the explicit sub-pages
        for sub_url in links_to_crawl:'''

content = content.replace(old_scrape, new_scrape)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Refactored leads_handler.py')
