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
        if leads_handler.is_restaurant_or_hotel(dl["type"]):
            if not dl["website"] or not dl["website"].strip():
                lead_id = database.add_lead(
                    name=dl["name"],
                    email=dl["email"],
                    website=dl["website"],
                    lead_type=dl["type"],
                    address=dl["address"],
                    source=dl["source"],
                    status="pending"
                )
                if lead_id:
                    added_count += 1
                    
    print(f"[SUCCESS] Lead discovery cycle finished. Added {added_count} new leads to database.")

def process_single_lead_pipeline():
    print("[INFO] Running single lead processing pipeline (email lookup)...")
    
    conn = database.get_db_connection()
    cursor = conn.cursor()
    try:
        # Find the first lead that is pending/discovered and doesn't have an email yet
        cursor.execute("""
        SELECT * FROM leads 
        WHERE status IN ('pending', 'discovered') 
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
        return
        
    lead_dict = dict(lead)
    lead_id = lead_dict["id"]
    
    # 1. Double check type is restaurant or hotel
    if not leads_handler.is_restaurant_or_hotel(lead_dict["type"]):
        print(f"[PIPELINE] Skipping '{lead_dict['name']}' (Type: {lead_dict['type']}) - not a restaurant or hotel.")
        database.update_lead_status(lead_id, "skipped_type")
        return
        
    # 2. Double check if website already exists
    if lead_dict["website"] and lead_dict["website"].strip():
        print(f"[PIPELINE] Skipping '{lead_dict['name']}' - website already exists ({lead_dict['website']}).")
        database.update_lead_status(lead_id, "skipped_website")
        return
        
    # 3. Search for email
    print(f"[PIPELINE] Searching email for '{lead_dict['name']}'...")
    email = leads_handler.search_duckduckgo_for_email(lead_dict["name"], lead_dict["address"])
    if email:
        print(f"[PIPELINE] Found email '{email}' for '{lead_dict['name']}'.")
        database.update_lead_email(lead_id, email)
        database.update_lead_status(lead_id, "pending_outreach")
    else:
        print(f"[PIPELINE] No email found for '{lead_dict['name']}'. Marking as no_email_found.")
        database.update_lead_status(lead_id, "no_email_found")
