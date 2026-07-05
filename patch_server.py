import re

with open('src/server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the database query
text = text.replace('request_date=CURRENT_DATE', 'request_date=CURRENT_DATE::date')

# Replace the scheduler loop
scheduler_code = '''
last_google_run = 0
last_email_run = 0
last_reply_check = 0

# Periodic Scheduler Loop
def scheduler_loop():
    print("[INFO] Background scheduler loop activated.")
    global last_google_run, last_email_run, last_reply_check
    
    # Small startup delay to allow server initialization
    import time, threading
    time.sleep(5)

    while True:
        now = time.time()
        
        # 1. Lead discovery (every 45 mins = 2700s)
        google_time_left = int(2700 - (now - last_google_run))
        if last_google_run == 0 or google_time_left <= 0:
            last_google_run = now
            
            # Check daily limits
            todays_leads = 0
            try:
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM leads WHERE created_at::date = CURRENT_DATE")
                row = cursor.fetchone()
                if row:
                    todays_leads = row['count'] if isinstance(row, dict) or hasattr(row, 'keys') else row[0]
                conn.close()
            except Exception as e:
                print("[ERROR] Limit check failed:", e)
                
            if todays_leads >= 100:
                print("[LIMIT] Daily lead limit reached")
            else:
                from src.pipeline import run_discovery_cycle
                threading.Thread(target=run_discovery_cycle, daemon=True).start()
        else:
            print(f"[GOOGLE] Skipped. Next run in {google_time_left // 60} minutes")

        # 2. Email processing (every 5 mins = 300s)
        if last_email_run == 0 or now - last_email_run >= 300:
            last_email_run = now
            print("[EMAIL] Processing pending leads")
            from src.pipeline import process_leads_pipeline
            threading.Thread(target=process_leads_pipeline, daemon=True).start()
            
        # 3. Reply checker (every 30 mins = 1800s)
        if last_reply_check == 0 or now - last_reply_check >= 1800:
            last_reply_check = now
            try:
                threading.Thread(target=check_replies_job, daemon=True).start()
            except Exception as e:
                print(f"[ERROR] Failed to start reply checker thread: {e}")

        # Sleep a short while before checking timers again
        time.sleep(60)

@app.on_event("startup")
'''

# Find everything from "last_discovery_check = 0" or "pipeline_running = False" down to "@app.on_event("startup")"
text = re.sub(r'pipeline_running = False.*?@app.on_event\("startup"\)', scheduler_code, text, flags=re.DOTALL)

with open('src/server.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patched server.py successfully")
