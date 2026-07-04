import argparse
import sys
from src import database, leads_handler, email_handler, replies_handler

def run_outreach():
    print("Starting outreach run...")
    leads = database.get_pending_outreach_leads()
    print(f"Found {len(leads)} pending leads with emails and no website.")
    
    for lead in leads:
        lead_dict = dict(lead)
        subject, text, html = email_handler.build_outreach_message(lead_dict)
        try:
            print(f"Sending outreach to {lead_dict['name']} ({lead_dict['email']})...")
            message_id = email_handler.send_email(
                to_email=lead_dict["email"],
                subject=subject,
                text_content=text,
                html_content=html
            )
            
            # Log sent outreach in database
            database.log_message(
                lead_id=lead_dict["id"],
                message_id=message_id,
                direction="outbound",
                subject=subject,
                body=text
            )
            
            # Update status to 'outreached'
            database.update_lead_status(lead_dict["id"], "outreached")
            print(f"Outreach logged successfully for {lead_dict['email']}.")
            
        except Exception as e:
            print(f"Failed to send outreach to {lead_dict['email']}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Client Outreach and Follow-up Bot")
    parser.add_argument("--init-db", action="store_true", help="Initialize the SQLite database")
    parser.add_argument("--find-leads", action="store_true", help="Find and store leads from CSV & Google Places")
    parser.add_argument("--outreach", action="store_true", help="Send outreach to pending leads without websites")
    parser.add_argument("--check-replies", action="store_true", help="Check IMAP for replies and follow up")
    parser.add_argument("--all", action="store_true", help="Run find-leads, outreach, and check-replies")
    parser.add_argument("--server", action="store_true", help="Run the FastAPI web server for 24/7 execution and dashboard monitoring")

    args = parser.parse_args()

    # Always initialize DB if it doesn't exist
    database.init_db()

    if args.init_db:
        print("Database initialized.")
        return

    if args.server:
        import uvicorn
        print("Starting FastAPI dashboard server on http://localhost:8000...")
        uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=False)
        return

    if args.all:
        args.find_leads = True
        args.outreach = True
        args.check_replies = True

    if not (args.find_leads or args.outreach or args.check_replies or args.server):
        parser.print_help()
        return

    if args.find_leads:
        print("\n--- Running Lead Discovery & Enrichment ---")
        leads_handler.process_and_store_leads()

    if args.outreach:
        print("\n--- Running Email Outreach ---")
        run_outreach()

    if args.check_replies:
        print("\n--- Running Reply Checker ---")
        replies_handler.check_and_handle_replies()

    print("\nRun complete.")

if __name__ == "__main__":
    main()
