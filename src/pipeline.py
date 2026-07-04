import os
from . import database
from . import leads_handler
from . import openai_handler
from . import email_handler
from . import config

def process_single_lead_pipeline():
    print("[INFO] Running single lead processing pipeline...")
    
    # Loop until we either successfully process one lead or run out of unprocessed ones
    while True:
        # Get next lead with status 'pending' or 'discovered'
        lead = database.get_next_unprocessed_lead()
        
        if not lead:
            # Check daily API usage count before querying Google Places API
            if database.get_daily_api_count("google_places") >= 250:
                print("[WARNING] Google Places daily rate limit (250) reached. Cannot fetch new leads.")
                break
                
            print("[INFO] No unprocessed leads in cache. Fetching from Google Places...")
            discovered_leads = leads_handler.discover_leads_from_google_places()
            if not discovered_leads:
                print("[INFO] No leads returned from Google Places.")
                break
                
            # Store discovered leads in DB
            for dl in discovered_leads:
                database.add_lead(
                    name=dl["name"],
                    email=dl["email"],
                    website=dl["website"],
                    lead_type=dl["type"],
                    address=dl["address"],
                    source=dl["source"],
                    status="discovered"
                )
            
            # Retrieve the lead again from DB
            lead = database.get_next_unprocessed_lead()
            if not lead:
                print("[INFO] Still no unprocessed leads after Google Places query.")
                break
        
        lead_dict = dict(lead)
        lead_id = lead_dict["id"]
        
        # 1. Check if business is a restaurant or hotel
        if not leads_handler.is_restaurant_or_hotel(lead_dict["type"]):
            print(f"[PIPELINE] Skipping '{lead_dict['name']}' (Type: {lead_dict['type']}) - not a restaurant or hotel.")
            database.update_lead_status(lead_id, "skipped_type")
            continue # Try the next lead in the loop
            
        # 2. Check if business has a website
        if lead_dict["website"] and lead_dict["website"].strip():
            print(f"[PIPELINE] Skipping '{lead_dict['name']}' - website already exists ({lead_dict['website']}).")
            database.update_lead_status(lead_id, "skipped_website")
            continue # Try the next lead in the loop
            
        # 3. Search for email if missing
        email = lead_dict["email"]
        if not email:
            print(f"[PIPELINE] Searching email for '{lead_dict['name']}'...")
            email = leads_handler.search_duckduckgo_for_email(lead_dict["name"], lead_dict["address"])
            if email:
                print(f"[PIPELINE] Found email '{email}' for '{lead_dict['name']}'.")
                database.update_lead_email(lead_id, email)
                lead_dict["email"] = email
            else:
                print(f"[PIPELINE] No email found for '{lead_dict['name']}'. Marking as no_email_found.")
                database.update_lead_status(lead_id, "no_email_found")
                return # Stop here, wait for next 5-min slot
                
        # 4. We have email, no website, type matches. Send outreach!
        # Check NVIDIA daily API limit
        daily_nvidia = database.get_daily_api_count("nvidia")
        if daily_nvidia >= 500:
            print("[WARNING] NVIDIA daily limit (500) reached. Postponing outreach.")
            return # Stop here, wait for next 5-min slot
            
        print(f"[PIPELINE] Generating outreach email for '{lead_dict['name']}' ({lead_dict['email']})...")
        subject, body = openai_handler.generate_outreach_email(
            lead_name=lead_dict["name"],
            lead_type=lead_dict["type"],
            lead_address=lead_dict["address"]
        )
        
        html_body = f"<p>{body.replace(chr(10), '<br/>')}</p>"
        
        try:
            print(f"[PIPELINE] Sending outreach email to {lead_dict['email']}...")
            message_id = email_handler.send_email(
                to_email=lead_dict["email"],
                subject=subject,
                text_content=body,
                html_content=html_body
            )
            
            database.log_message(
                lead_id=lead_id,
                message_id=message_id,
                direction="outbound",
                subject=subject,
                body=body
            )
            
            database.update_lead_status(lead_id, "outreached")
            print(f"[SUCCESS] Outreach completed for {lead_dict['name']}.")
            
        except Exception as e:
            print(f"[ERROR] Failed to send outreach to {lead_dict['email']}: {e}")
            database.update_lead_status(lead_id, "failed_outreach")
            
        return # Done with processing a single business for this 5-min slot
