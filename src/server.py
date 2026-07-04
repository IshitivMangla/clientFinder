import sys
import os
import time
import datetime
import threading
from fastapi import FastAPI, HTTPException, Cookie, Response, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from src import config

# Adjust path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import database, leads_handler, email_handler, replies_handler
from src.pipeline import process_single_lead_pipeline

# Initialize database tables on startup
database.init_db()

app = FastAPI(title="Outreach Bot API", version="2.0.0")

# Scheduler state variables
last_checked_time = None
active_tasks = {
    "check_replies": False,
    "find_leads": False,
    "outreach": False
}
cancel_requests = {
    "check_replies": False,
    "find_leads": False,
    "outreach": False
}

# Outreach function helper
def run_outreach_internal():
    print("Starting outreach run...")
    leads = database.get_pending_outreach_leads()
    print(f"Found {len(leads)} pending leads with emails and no website.")
    
    for lead in leads:
        if cancel_requests["outreach"]:
            print("[INFO] Outreach run cancelled by user.")
            break
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

# Background worker threads
def check_replies_job():
    global last_checked_time
    if active_tasks["check_replies"]:
        return
    active_tasks["check_replies"] = True
    cancel_requests["check_replies"] = False
    print("[INFO] Starting email replies checker...")
    try:
        replies_handler.check_and_handle_replies(is_cancelled=lambda: cancel_requests["check_replies"])
        last_checked_time = time.time()
        print("[SUCCESS] Reply check run complete.")
    except Exception as e:
        print(f"[ERROR] Reply check failed: {e}")
    finally:
        active_tasks["check_replies"] = False

def find_leads_job():
    if active_tasks["find_leads"]:
        return
    active_tasks["find_leads"] = True
    cancel_requests["find_leads"] = False
    print("[INFO] Starting lead discovery...")
    try:
        leads_handler.process_and_store_leads(is_cancelled=lambda: cancel_requests["find_leads"])
        print("[SUCCESS] Lead discovery complete.")
    except Exception as e:
        print(f"[ERROR] Lead discovery failed: {e}")
    finally:
        active_tasks["find_leads"] = False

def outreach_job():
    if active_tasks["outreach"]:
        return
    active_tasks["outreach"] = True
    cancel_requests["outreach"] = False
    print("[INFO] Starting email outreach...")
    try:
        run_outreach_internal()
        print("[SUCCESS] Email outreach complete.")
    except Exception as e:
        print(f"[ERROR] Email outreach failed: {e}")
    finally:
        active_tasks["outreach"] = False

# Periodic Scheduler Loop
def scheduler_loop():
    print("[INFO] Background scheduler loop activated.")
    last_reply_check = 0
    last_lead_process = 0
    
    # Small startup delay to allow server initialization
    time.sleep(5)
    
    while True:
        now = time.time()
        
        # 1. Run lead pipeline every 5 minutes (300 seconds)
        if now - last_lead_process >= 300:
            last_lead_process = now
            try:
                threading.Thread(target=process_single_lead_pipeline, daemon=True).start()
            except Exception as e:
                print(f"[ERROR] Failed to start lead pipeline thread: {e}")
                
        # 2. Run reply checker every 1 hour (3600 seconds)
        if now - last_reply_check >= 3600:
            last_reply_check = now
            try:
                threading.Thread(target=check_replies_job, daemon=True).start()
            except Exception as e:
                print(f"[ERROR] Failed to start reply checker thread: {e}")
                
        time.sleep(10)

# Start scheduler thread
scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
scheduler_thread.start()

# API Auth Dependency
def verify_api_auth(auth_token: str = Cookie(None)):
    expected_password = config.DASHBOARD_PASSWORD
    if not expected_password:
        return
    if auth_token != expected_password:
        raise HTTPException(status_code=401, detail="Unauthorized")

# API Endpoints & Auth Routes
@app.get("/", response_class=HTMLResponse)
def get_dashboard(auth_token: str = Cookie(None)):
    expected_password = config.DASHBOARD_PASSWORD
    if expected_password and auth_token != expected_password:
        login_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login.html")
        if not os.path.exists(login_path):
            return HTMLResponse(content="<h1>Outreach Bot Login</h1><p>login.html template file not found</p>", status_code=404)
        with open(login_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
            
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
    if not os.path.exists(dashboard_path):
        raise HTTPException(status_code=404, detail="Dashboard UI file not found")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/login")
def login(response: Response, password: str = Form(...)):
    expected_password = config.DASHBOARD_PASSWORD
    if not expected_password:
        return {"message": "Bypassed"}
    if password != expected_password:
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    response.set_cookie(
        key="auth_token",
        value=password,
        httponly=True,
        max_age=30 * 24 * 3600, # 30 days
        samesite="lax"
    )
    return {"message": "Success"}

@app.get("/logout")
def logout(response: Response):
    response.delete_cookie("auth_token")
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/status", dependencies=[Depends(verify_api_auth)])
def get_status():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT count(*) FROM leads")
    total_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT count(*) FROM leads WHERE status = 'outreached'")
    outreached = cursor.fetchone()[0]
    
    cursor.execute("SELECT count(*) FROM leads WHERE status = 'engaged'")
    engaged = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "stats": {
            "total_leads": total_leads,
            "outreached": outreached,
            "engaged": engaged
        },
        "last_checked_time": last_checked_time,
        "active_tasks": active_tasks
    }

@app.get("/api/leads", dependencies=[Depends(verify_api_auth)])
def get_leads():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    leads = [dict(row) for row in rows]
    conn.close()
    return {"leads": leads}



@app.post("/api/tasks/check-replies", dependencies=[Depends(verify_api_auth)])
def trigger_check_replies():
    if active_tasks["check_replies"]:
        raise HTTPException(status_code=400, detail="Reply checker is already running")
    threading.Thread(target=check_replies_job, daemon=True).start()
    return {"message": "Email reply checker started in the background."}

@app.post("/api/tasks/find-leads", dependencies=[Depends(verify_api_auth)])
def trigger_find_leads():
    if active_tasks["find_leads"]:
        raise HTTPException(status_code=400, detail="Lead discovery is already running")
    threading.Thread(target=find_leads_job, daemon=True).start()
    return {"message": "Lead discovery started in the background."}

@app.post("/api/tasks/outreach", dependencies=[Depends(verify_api_auth)])
def trigger_outreach():
    if active_tasks["outreach"]:
        raise HTTPException(status_code=400, detail="Email outreach is already running")
    threading.Thread(target=outreach_job, daemon=True).start()
    return {"message": "Outreach email campaign started in the background."}

@app.post("/api/tasks/stop/{task_name}", dependencies=[Depends(verify_api_auth)])
def stop_task(task_name: str):
    if task_name not in cancel_requests:
        raise HTTPException(status_code=400, detail="Invalid task name")
    if not active_tasks[task_name]:
        raise HTTPException(status_code=400, detail=f"Task '{task_name}' is not running")
        
    cancel_requests[task_name] = True
    return {"message": f"Cancellation request sent for task '{task_name}'."}
