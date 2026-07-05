import os
import re
import urllib.parse
import csv
from pathlib import Path
import requests

import time

def safe_request(url, retries=2, **kwargs):
    for attempt in range(retries):
        try:
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 10
            return requests.get(url, **kwargs)
        except Exception as e:
            print(f"Request to {url} failed: {e}. Retrying {attempt+1}/{retries}...")
            time.sleep(5)
    return None
from bs4 import BeautifulSoup
from . import config
from . import database


def valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def clean_business_name(name):
    """Strip legal entities, brand names, and special chars for better search results."""
    # Remove by Wyndham, by IHG, Tribute Portfolio, LLC, Inc
    cleaned = re.sub(r'(?i)\b(?:by Wyndham|by IHG|Tribute Portfolio|LLC|Inc)\b', '', name)
    # Remove commas, hyphens, special chars
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def get_us_locations():
    # us_locations.csv is in the project root
    file_path = Path(__file__).resolve().parent.parent / "us_locations.csv"
    if not file_path.exists():
        print(f"[WARNING] us_locations.csv not found at {file_path}")
        return []
    
    locations = []
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("city") and row.get("state") and row.get("latitude") and row.get("longitude"):
                    locations.append({
                        "city": row["city"].strip(),
                        "state": row["state"].strip(),
                        "latitude": row["latitude"].strip(),
                        "longitude": row["longitude"].strip()
                    })
    except Exception as e:
        print(f"[ERROR] Failed to read us_locations.csv: {e}")
    return locations

def get_next_search_location(locations):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT address FROM leads")
        addresses = [row[0] for row in cursor.fetchall() if row[0]]
    except Exception as e:
        print(f"[ERROR] Failed to query lead addresses for location balancing: {e}")
        addresses = []
    finally:
        conn.close()
    
    counts = {}
    for loc in locations:
        city = loc["city"]
        state = loc["state"]
        match_str = f"{city}, {state}".lower()
        counts[match_str] = sum(1 for addr in addresses if match_str in addr.lower())
        
    best_loc = min(locations, key=lambda loc: counts[f"{loc['city']}, {loc['state']}".lower()])
    return best_loc

def get_next_search_query():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT count(*) FROM leads WHERE type LIKE '%restaurant%'")
        restaurant_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM leads WHERE type LIKE '%hotel%' OR type LIKE '%lodging%' OR type LIKE '%motel%' OR type LIKE '%inn%'")
        hotel_count = cursor.fetchone()[0]
    except Exception as e:
        print(f"[ERROR] Failed to query leads type count: {e}")
        restaurant_count = 0
        hotel_count = 0
    finally:
        conn.close()
        
    if restaurant_count <= hotel_count:
        return "restaurant"
    else:
        return "hotel"

# Disable SSL verification warnings if verification is disabled in config
if not config.VERIFY_SSL:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def is_restaurant_or_hotel(lead_type):
    if not lead_type:
        return False
    type_lower = lead_type.lower()
    keywords = ["restaurant", "food", "cafe", "bar", "pub", "meal_takeaway", "meal_delivery", "hotel", "lodging", "motel", "inn", "resort", "hostel"]
    return any(kw in type_lower for kw in keywords)

def discover_leads_from_google_places(is_cancelled=None):
    if not config.GOOGLE_PLACES_API_KEY:
        print("Google Places API key is not configured.")
        return []

    # Check daily limit (max 250)
    if database.get_daily_api_count("google_places") >= 250:
        print("[WARNING] Google Places daily rate limit (250) reached. Cannot make request.")
        return []

    locations = get_us_locations()
    if not locations:
        if not config.SEARCH_LOCATION:
            print("Google Places search location is not configured and us_locations.csv is missing/empty.")
            return []
        search_loc = config.SEARCH_LOCATION
        print(f"[INFO] Using configured fallback SEARCH_LOCATION: {search_loc}")
    else:
        loc = get_next_search_location(locations)
        search_loc = f"{loc['latitude']},{loc['longitude']}"
        print(f"[INFO] Selected next search location: {loc['city']}, {loc['state']} ({search_loc})")

    query = get_next_search_query()
    print(f"[INFO] Selected next search query: {query}")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "key": config.GOOGLE_PLACES_API_KEY,
        "query": query,
        "location": search_loc,
        "radius": config.SEARCH_RADIUS
    }

    try:
        if not database.enforce_rate_limit("google_places", 300, is_cancelled):
            return []
        database.increment_api_usage("google_places")
        response = safe_request(
     url, params=params,
     timeout=30,
     verify=config.VERIFY_SSL
 )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        
        leads = []
        for item in results:
            types_list = item.get("types") or []
            lead_type = ", ".join(types_list) if types_list else "business"
            
            place_id = item.get("place_id")
            website = item.get("website", "").strip()
            
            # TextSearch rarely returns website. Fetch Place Details to get it!
            if not website and place_id:
                try:
                    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                    details_params = {
                        "place_id": place_id,
                        "fields": "website",
                        "key": config.GOOGLE_PLACES_API_KEY
                    }
                    det_res = safe_request(
     details_url, params=details_params,
     timeout=30,
     verify=config.VERIFY_SSL
 )
                    if det_res is None:
                        continue
                    if det_res.status_code == 200:
                        det_data = det_res.json()
                        if det_data.get("result") and det_data["result"].get("website"):
                            website = det_data["result"]["website"].strip()
                except Exception as e:
                    print(f"Failed to fetch place details for {place_id}: {e}")
            
            leads.append({
                "name": item.get("name", "").strip(),
                "address": item.get("formatted_address", "").strip(),
                "website": website,
                "type": lead_type,
                "source": "google_places",
                "email": ""
            })
        return leads
    except Exception as e:
        print(f"Google Places API error: {e}")
        return []

def extract_emails_from_text(text, exclude_domains):
    email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}")
    emails = set()
    found = email_regex.findall(text)
    for email in found:
        if not any(email.lower().endswith(dom) for dom in exclude_domains):
                if valid_email(email):
                    emails.add(email.lower())
    return emails

def scrape_email_from_website(url):
    """
    Dynamically scrape a website's homepage and follow common contact paths 
    to extract email addresses.
    """
    if not url:
        return None
        
    if not url.startswith('http'):
        url = 'https://' + url
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    exclude_domains = [
        "brave.com", "google.com", "duckduckgo.com", "microsoft.com", "bing.com", 
        "yahoo.com", "ask.com", "yandex.ru", ".png", ".jpg", ".jpeg", ".gif", 
        ".webp", ".svg", ".js", ".css", ".ico", ".woff", ".woff2", ".ttf", ".eot",
        "sentry.io", "wix.com", "squarespace.com", "shopify.com"
    ]
    
    found_emails = set()
    try:
        response = safe_request(
     url, headers=headers,
     timeout=30,
     verify=config.VERIFY_SSL
 )
        if response is None:
            return None
        if response.status_code != 200:
            return None
            
        # 1. Check homepage body
        found_emails.update(extract_emails_from_text(response.text, exclude_domains))
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 2. Check for explicit mailto: links (often obfuscated from regex)
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().startswith('mailto:'):
                email = href[7:].split('?')[0].strip()
                if email and not any(email.lower().endswith(dom) for dom in exclude_domains):
                    found_emails.add(email.lower())
                    
        if found_emails:
            return list(found_emails)[0]
            
        # 3. Explicitly scrape hardcoded contact paths as requested
        paths = ['/contact', '/contact-us', '/about', '/team']
        base_url = url.rstrip('/')
        links_to_crawl = [base_url + p for p in paths]
        
        # Crawl the explicit sub-pages
        for sub_url in links_to_crawl:
            try:
                sub_res = safe_request(
     sub_url, headers=headers,
     timeout=30,
     verify=config.VERIFY_SSL
 )
                if sub_res is None:
                    continue
                if sub_res.status_code == 200:
                    found_emails.update(extract_emails_from_text(sub_res.text, exclude_domains))
                    # Check mailto on subpages too
                    sub_soup = BeautifulSoup(sub_res.text, "html.parser")
                    for a in sub_soup.find_all('a', href=True):
                        href = a['href']
                        if href.lower().startswith('mailto:'):
                            email = href[7:].split('?')[0].strip()
                            if email and not any(email.lower().endswith(dom) for dom in exclude_domains):
                                found_emails.add(email.lower())
                                
                if found_emails:
                    break
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Failed to scrape website {url}: {e}")
        
    return list(found_emails)[0] if found_emails else None

def search_duckduckgo_for_email(business_name, address):
    business_name = clean_business_name(business_name)
    # Extract clean address components
    street = ""
    city = ""
    if address:
        parts = [p.strip() for p in address.split(",") if p.strip()]
        if len(parts) > 0:
            street = parts[0]
        if len(parts) > 1:
            city = parts[1]
            
    # Build short fallback queries
    queries = []
    if city:
        queries.append(f"{business_name} {city} contact email")
    queries.append(f"{business_name} contact email")
    
    # De-duplicate queries
    seen = set()
    clean_queries = []
    for q in queries:
        if q.lower() not in seen:
            seen.add(q.lower())
            clean_queries.append(q)
            
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    emails = set()
    email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}")
    
    # Exclude common domains that are search engines or asset files
    exclude_domains = [
        "brave.com", "google.com", "duckduckgo.com", "microsoft.com", "bing.com", 
        "yahoo.com", "ask.com", "yandex.ru", ".png", ".jpg", ".jpeg", ".gif", 
        ".webp", ".svg", ".js", ".css", ".ico", ".woff", ".woff2", ".ttf", ".eot"
    ]
    
    for query in clean_queries:
        escaped_query = urllib.parse.quote(query)
        
        # Try Yahoo Search first (less aggressive bot blocking than Brave/DDG)
        try:
            yahoo_url = f"https://search.yahoo.com/search?p={escaped_query}"
            response = safe_request(
     yahoo_url, headers=headers,
     timeout=30,
     verify=config.VERIFY_SSL
 )
            if response is None:
                return None
            if response.status_code == 200:
                found = email_regex.findall(response.text)
                for email in found:
                    if not any(email.lower().endswith(dom) for dom in exclude_domains):
                            if valid_email(email):
                                emails.add(email.lower())
                if emails:
                    break
        except Exception as e:
            print(f"Yahoo Search error for query '{query}': {e}")
            
        # Try Brave Search
        try:
            brave_url = f"https://search.brave.com/search?q={escaped_query}"
            response = safe_request(
     brave_url, headers=headers,
     timeout=30,
     verify=config.VERIFY_SSL
 )
            if response is None:
                return None
            if response.status_code == 200:
                found = email_regex.findall(response.text)
                for email in found:
                    if not any(email.lower().endswith(dom) for dom in exclude_domains):
                            if valid_email(email):
                                emails.add(email.lower())
                if emails:
                    break
        except Exception as e:
            print(f"Brave Search error for query '{query}': {e}")
            
        # Try DuckDuckGo fallback
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={escaped_query}"
            response = safe_request(
     ddg_url, headers=headers,
     timeout=30,
     verify=config.VERIFY_SSL
 )
            if response is None:
                return None
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                snippets = soup.find_all(class_="result__snippet")
                
                for snippet in snippets:
                    text = snippet.get_text()
                    found = email_regex.findall(text)
                    for email in found:
                        if not any(email.lower().endswith(dom) for dom in exclude_domains):
                                if valid_email(email):
                                    emails.add(email.lower())
                if emails:
                    break
        except Exception as e:
            print(f"DuckDuckGo error for query '{query}': {e}")
            
    return list(emails)[0] if emails else None

def filter_leads_without_website(leads):
    return [lead for lead in leads if not lead.get("website") and lead.get("email")]

def process_and_store_leads(is_cancelled=None):
    # Discover Google Places leads
    if config.GOOGLE_PLACES_API_KEY:
        discovered = discover_leads_from_google_places()
        print(f"Discovered {len(discovered)} leads from Google Places.")
        
        for lead in discovered:
            if is_cancelled and is_cancelled():
                print("[INFO] Lead processing cancelled by user.")
                break
            # Only process if business is a restaurant or hotel
            if not is_restaurant_or_hotel(lead["type"]):
                print(f"Skipping '{lead['name']}' (Type: {lead['type']}) - not a restaurant or hotel.")
                continue
            # Check if we already have this lead in the database
            existing = database.get_lead_by_email(lead["email"]) if lead.get("email") else None
            if not existing:
                print(f"Searching email for: {lead['name']}...")
                email = None
                
                # 1. Try website scraping
                if lead.get("website"):
                    print(f"Attempting to scrape website directly: {lead['website']}")
                    email = scrape_email_from_website(lead["website"])
                    
                # 2. Try DuckDuckGo / Brave search
                if not email:
                    print("Using search engine fallback...")
                    email = search_duckduckgo_for_email(lead["name"], lead["address"])
                    
                if email:
                    print(f"Found email: {email}")
                    lead["email"] = email
                else:
                    print("No email found.")
            
            if lead["email"]:
                database.add_lead(
                    name=lead["name"],
                    email=lead["email"],
                    website=lead["website"],
                    lead_type=lead["type"],
                    address=lead["address"],
                    source=lead["source"]
                )

def save_interested_lead_to_db(lead, negotiated_price):
    from . import database
    database.save_interested_lead_to_db(lead, negotiated_price)
