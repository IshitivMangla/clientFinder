import os

path = 'src/server.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add pathlib and BASE_DIR
if 'from pathlib import Path' not in content:
    # Insert after fastapi imports
    content = content.replace('from fastapi import FastAPI', 'from pathlib import Path\nfrom fastapi import FastAPI')
    content = content.replace('app = FastAPI(', 'BASE_DIR = Path(__file__).resolve().parent\n\napp = FastAPI(')

# 2. Fix the static mount
old_mount1 = 'app.mount("/static", StaticFiles(directory="src/static"), name="static")'
old_mount2 = 'app.mount("/static", StaticFiles(directory="static"), name="static")'
new_mount = 'app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")'

if old_mount1 in content:
    content = content.replace(old_mount1, new_mount)
elif old_mount2 in content:
    content = content.replace(old_mount2, new_mount)

# 3. Fix the favicon endpoint
old_favicon_func = '''
@app.get("/favicon.ico")
def favicon():
    return FileResponse("src/static/favicon.ico")
'''
new_favicon_func = '''
@app.get("/favicon.ico")
def favicon():
    favicon_path = BASE_DIR / "static/favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return {"status": "no icon"}
'''
if old_favicon_func.strip() in content:
    content = content.replace(old_favicon_func.strip(), new_favicon_func.strip())
else:
    # try replacing line by line
    content = content.replace('return FileResponse("src/static/favicon.ico")', 'return FileResponse(BASE_DIR / "static/favicon.ico")')

# 4. Add the health endpoint
health_func = '''
@app.get("/health")
def health():
    return {
        "status": "ok"
    }
'''
if '@app.get("/health")' not in content:
    content = content.replace('@app.get("/favicon.ico")', health_func + '\n@app.get("/favicon.ico")')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated server.py")
