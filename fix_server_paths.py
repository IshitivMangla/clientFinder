import os

path = 'src/server.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix the startup function
old_startup = '''
@app.on_event("startup")
def start_scheduler():
    import threading
    thread = threading.Thread(
        target=scheduler_loop,
        daemon=True
    )
    thread.start()
'''

if 'def start_scheduler():' in content:
    content = content.replace('def start_scheduler():', 'def startup():')

# 2. Fix the get_dashboard endpoint
old_get_dashboard = '''
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
        return HTMLResponse(content="<h1>Outreach Bot</h1><p>dashboard.html template file not found</p>", status_code=404)
        
    with open(dashboard_path, "r", encoding="utf-8", errors="replace") as f:
        return HTMLResponse(content=f.read())
'''

new_get_dashboard = '''
@app.get("/")
def dashboard(auth_token: str = Cookie(None)):
    expected_password = config.DASHBOARD_PASSWORD
    if expected_password and auth_token != expected_password:
        login_path = BASE_DIR / "login.html"
        if not login_path.exists():
            return HTMLResponse(content="<h1>Outreach Bot Login</h1><p>login.html template file not found</p>", status_code=404)
        with open(login_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
            
    dashboard_path = BASE_DIR / "dashboard.html"
    if not dashboard_path.exists():
        return HTMLResponse(content="<h1>Outreach Bot</h1><p>dashboard.html template file not found</p>", status_code=404)
        
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
'''

if 'def get_dashboard' in content:
    # We will use regex to find the block or just do string replacement
    import re
    # Match the get_dashboard function up to return HTMLResponse
    content = re.sub(r'@app\.get\("/", response_class=HTMLResponse\).*?return HTMLResponse\(content=f\.read\(\)\)', new_get_dashboard.strip(), content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated server.py startup and dashboard path")
