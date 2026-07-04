import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from . import config
from . import database

# Disable SSL verification warnings if verification is disabled in config
if not config.VERIFY_SSL:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def is_restaurant(lead_type):
    if not lead_type:
        return False
    type_lower = lead_type.lower()
    keywords = ["restaurant"]
    return any(kw in type_lower for kw in keywords)

def discover_leads_from_google_places():
    if not config.GOOGLE_PLACES_API_KEY or not config.SEARCH_LOCATION:
        print("Google Places API key or search location is not configured.")
        return []

    # Check daily limit (max 250)
    if database.get_daily_api_count("google_places") >= 250:
        print("[WARNING] Google Places daily rate limit (250) reached. Cannot make request.")
        return []

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "key": config.GOOGLE_PLACES_API_KEY,
        "query": config.SEARCH_QUERY,
        "location": config.SEARCH_LOCATION,
        "radius": config.SEARCH_RADIUS
    }

    try:
        database.enforce_rate_limit("google_places", 300)
        database.increment_api_usage("google_places")
        response = requests.get(url, params=params, timeout=15, verify=config.VERIFY_SSL)
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        
        leads = []
        for item in results:
            types_list = item.get("types") or []
            lead_type = ", ".join(types_list) if types_list else "business"
            
            leads.append({
                "name": item.get("name", "").strip(),
                "address": item.get("formatted_address", "").strip(),
                "website": item.get("website", "").strip(),
                "type": lead_type,
                "source": "google_places",
                "email": ""
            })
        return leads
    except Exception as e:
        print(f"Google Places API error: {e}")
        return []

def search_duckduckgo_for_email(business_name, address):
    query = f"{business_name} {address or ''} email".strip()
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    emails = set()
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=config.VERIFY_SSL)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            snippets = soup.find_all(class_="result__snippet")
            email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}")
            
            for snippet in snippets:
                text = snippet.get_text()
                found = email_regex.findall(text)
                for email in found:
                    if not any(email.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".js", ".css"]):
                        emails.add(email.lower())
    except Exception as e:
        print(f"Error searching email for {business_name}: {e}")
        
    return list(emails)[0] if emails else None

def filter_leads_without_website(leads):
    return [lead for lead in leads if not lead.get("website") and lead.get("email")]

def process_and_store_leads(is_cancelled=None):
    # Discover Google Places leads
    if config.GOOGLE_PLACES_API_KEY and config.SEARCH_LOCATION:
        discovered = discover_leads_from_google_places()
        print(f"Discovered {len(discovered)} leads from Google Places.")
        
        for lead in discovered:
            if is_cancelled and is_cancelled():
                print("[INFO] Lead processing cancelled by user.")
                break
            # Only process if business is a restaurant
            if not is_restaurant(lead["type"]):
                print(f"Skipping '{lead['name']}' (Type: {lead['type']}) - not a restaurant.")
                continue
            if not lead["website"]:
                # Check if we already have this lead in the database
                existing = database.get_lead_by_email(lead["email"]) if lead["email"] else None
                if not existing:
                    print(f"Searching email for: {lead['name']}...")
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
