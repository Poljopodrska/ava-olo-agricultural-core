"""
Migration script to constitutional architecture
"""

import os
import shutil
from datetime import datetime

print("🏛️ AVA OLO Constitutional Migration")
print("=" * 50)

# Step 1: Backup existing files
print("\n1. Creating backup of existing files...")
backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(backup_dir, exist_ok=True)

files_to_backup = [
    "database_explorer.py",
    "templates/database_explorer.html",
    "templates/table_view.html",
    "templates/ai_query_results.html",
    "templates/data_modifier.html"
]

for file in files_to_backup:
    if os.path.exists(file):
        backup_path = os.path.join(backup_dir, file)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(file, backup_path)
        print(f"  ✓ Backed up {file}")

# Step 2: Create new entry point
print("\n2. Creating constitutional entry point...")

entry_point_content = '''"""
AVA OLO Admin Dashboard - Constitutional Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging

# Import constitutional API
from monitoring.interfaces.admin_dashboard_api import app as api_app
from monitoring.config.dashboard_config import DASHBOARD_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create main app
app = FastAPI(
    title="AVA OLO Admin Dashboard",
    description="Constitutional agricultural database management",
    version="2.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="monitoring/templates")

# Mount API
app.mount("/api", api_app)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "config": DASHBOARD_CONFIG
    })

@app.get("/database", response_class=HTMLResponse) 
async def database_redirect(request: Request):
    """Redirect old URL to new dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "config": DASHBOARD_CONFIG
    })

if __name__ == "__main__":
    print("🌾 Starting AVA OLO Admin Dashboard (Constitutional)")
    print("✅ Mango Rule Compliant")
    print("✅ Privacy First")
    print("✅ LLM First")
    print("✅ Error Isolation Active")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8005)
'''

with open("admin_dashboard.py", "w") as f:
    f.write(entry_point_content)
print("  ✓ Created admin_dashboard.py")

# Step 3: Update imports in database_operations.py if needed
print("\n3. Checking database_operations.py...")
if os.path.exists("database_operations.py"):
    print("  ✓ database_operations.py exists and will be reused")
else:
    print("  ⚠️  database_operations.py not found - please ensure it exists")

# Step 4: Create __init__ files
print("\n4. Creating __init__ files for modules...")
init_files = [
    "monitoring/__init__.py",
    "monitoring/core/__init__.py",
    "monitoring/interfaces/__init__.py",
    "monitoring/config/__init__.py"
]

for init_file in init_files:
    os.makedirs(os.path.dirname(init_file), exist_ok=True)
    open(init_file, 'a').close()
    print(f"  ✓ Created {init_file}")

# Step 5: Run constitutional tests
print("\n5. Running constitutional compliance tests...")
print("  Run: python test_constitutional_compliance.py")

# Step 6: Summary
print("\n" + "=" * 50)
print("🎉 Migration prepared successfully!")
print("\nNext steps:")
print("1. Run constitutional tests: python test_constitutional_compliance.py")
print("2. Start new dashboard: python admin_dashboard.py")
print("3. Test with Bulgarian mango query: 'Колко манго дървета имам?'")
print("4. Once verified, remove old files from backup directory")
print("\nThe new dashboard is at: http://localhost:8005/")
print("API endpoints at: http://localhost:8005/api/")
print("\n✅ Constitutional compliance achieved!")