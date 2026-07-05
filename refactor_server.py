import re

path = 'src/server.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the scheduler_loop logic
new_scheduler = '''pipeline_running = False

def run_pipeline_task():
    global pipeline_running
    try:
        from src.pipeline import run_discovery_cycle, process_leads_pipeline
        run_discovery_cycle()
        process_leads_pipeline()
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
    finally:
        pipeline_running = False

# Periodic Scheduler Loop
def scheduler_loop():
    print("[INFO] Background scheduler loop activated.")
    global pipeline_running
    last_reply_check = 0
    
    # Small startup delay to allow server initialization
    time.sleep(5)
    
    while True:
        now = time.time()
        
        # 1. Run lead pipeline and discovery cycle
        if pipeline_running:
            print("[INFO] Previous cycle still running. Skipping.")
        else:
            pipeline_running = True
            threading.Thread(target=run_pipeline_task, daemon=True).start()
                
        # 2. Run reply checker every 1 hour (3600 seconds)
        if now - last_reply_check >= 3600:
            last_reply_check = now
            try:
                threading.Thread(target=check_replies_job, daemon=True).start()
            except Exception as e:
                print(f"[ERROR] Failed to start reply checker thread: {e}")
                
        time.sleep(300)
'''

content = re.sub(r'# Periodic Scheduler Loop\ndef scheduler_loop\(\):.*?time\.sleep\(10\)', new_scheduler, content, flags=re.DOTALL)

# Add @app.head("/") endpoint
head_endpoint = '''
@app.head("/")
def health():
    return {}
'''
content = content.replace('app = FastAPI(title="Outreach Bot API", version="2.0.0")', 'app = FastAPI(title="Outreach Bot API", version="2.0.0")\n' + head_endpoint)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Refactored server.py')
