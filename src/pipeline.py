import os
from . import database
from . import leads_handler
from . import openai_handler
from . import email_handler
from . import config

def run_discovery_cycle():
    print("[INFO] Running background lead discovery cycle...")
    
    # Check daily API usage count before querying Google Places API
    if database.get_daily_api_count("google_places") >= 250:
        print("[WARNING] Google Places daily rate limit (250) reached. Cannot fetch new leads.")
        return
        
    print("[INFO] Fetching new leads from Google Places...")
    discovered_leads = leads_handler.discover_leads_from_google_places()
    if not discovered_leads:
        print("[INFO] No leads returned from Google Places.")
        return
        
    added_count = 0
    for dl in discovered_leads:
        if not leads_handler.is_restaurant_or_hotel(dl["type"]):
            continue  # Only store restaurants and hotels
            
        has_website = bool(dl.get("website") and dl["website"].strip())
        # Store ALL restaurants and hotels regardless of website status
        status = "has_website" if has_website else "pending"
        lead_id = database.add_lead(
            name=dl["name"],
            email=dl.get("email", ""),
            website=dl.get("website", ""),
            lead_type=dl["type"],
            address=dl["address"],
            source=dl["source"],
            status=status
        )
        if lead_id:
            added_count += 1
                    
    print(f"[SUCCESS] Lead discovery cycle finished. Added {added_count} new leads to database.")


def process_leads_pipeline():
    """Find email for leads — prioritises no-website leads but also picks up has_website leads."""
    print("[INFO] Running lead processing pipeline (email lookup)...")
    
    import time
    for _ in range(15):
        conn = database.get_db_connection()
        cursor = conn.cursor()
        try:
            # Priority 1: pending leads (no website) with no email
            cursor.execute("""
            SELECT * FROM leads 
            WHERE status IN ('pending', 'discovered') 
              AND (email IS NULL OR email = '')
            ORDER BY id ASC LIMIT 1
            """)
            lead = cursor.fetchone()

            # Priority 2: has_website leads that still have no email
            if not lead:
                cursor.execute("""
                SELECT * FROM leads 
                WHERE status = 'has_website'
                  AND (email IS NULL OR email = '')
                ORDER BY id ASC LIMIT 1
                """)
                lead = cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] Failed to fetch next lead for processing: {e}")
            lead = None
        finally:
            conn.close()
            
        if not lead:
            print("[INFO] No leads in database needing email lookup.")
            break
            
        lead_dict = dict(lead)
        lead_id = lead_dict["id"]
        
        # 1. Double check type is restaurant or hotel
        if not leads_handler.is_restaurant_or_hotel(lead_dict["type"]):
            print(f"[PIPELINE] Skipping '{lead_dict['name']}' (Type: {lead_dict['type']}) - not a restaurant or hotel.")
            database.update_lead_status(lead_id, "skipped_type")
            continue
            
        # 2. Search for email
        print(f"[PIPELINE] Searching email for '{lead_dict['name']}'...")
        email = None
        
        # 2a. Try direct website scraping first if available
        website = lead_dict.get("website")
        if website:
            print(f"[PIPELINE] Attempting to scrape website directly: {website}")
            email = leads_handler.scrape_email_from_website(website)
            
        # 2b. Fallback to DuckDuckGo/Brave Search
        if not email:
            print(f"[PIPELINE] Using search engine fallback...")
            email = leads_handler.search_duckduckgo_for_email(lead_dict["name"], lead_dict["address"])
        if email:
            print(f"[PIPELINE] Found email '{email}' for '{lead_dict['name']}'.")
            database.update_lead_email(lead_id, email)
            # Only set pending_outreach for no-website leads; keep has_website status for others
            if lead_dict["status"] != "has_website":
                database.update_lead_status(lead_id, "pending_outreach")
        else:
            print(f"[PIPELINE] No email found for '{lead_dict['name']}'. Marking as no_email_found.")
            database.update_lead_status(lead_id, "no_email_found")
            
        # Small delay to avoid rate limiting
        time.sleep(2)
