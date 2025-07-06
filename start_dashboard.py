#!/usr/bin/env python3
"""
AVA OLO Dashboard - Simple Start Script
One-click dashboard launcher with setup validation
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

def check_requirements():
    """Check if basic requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    required_files = [
        'monitoring_api.py',
        'explorer_api.py', 
        'monitoring_dashboard.html',
        'database_explorer.html',
        'config.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        print("Please ensure you're in the AVA OLO project directory")
        return False
    
    # Check Python packages
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pandas
        print("✅ Required packages available")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def setup_environment():
    """Set up environment if needed"""
    env_file = Path('.env')
    env_example = Path('env_example.txt')
    
    if not env_file.exists() and env_example.exists():
        print("⚙️ Setting up environment file...")
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("📝 Please edit .env with your database credentials")
        return False
    
    return True

def main():
    """Main launcher"""
    print("""
    🌾 AVA OLO Dashboard Launcher
    ═══════════════════════════════
    Croatian Agricultural Virtual Assistant
    """)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n⚠️  Please configure .env file with your database settings:")
        print("   DATABASE_URL=postgresql://user:pass@localhost:5432/ava_olo")
        print("   DB_HOST=localhost")
        print("   DB_NAME=ava_olo") 
        print("   DB_USER=postgres")
        print("   DB_PASSWORD=your_password")
        print("\nThen run this script again.")
        sys.exit(1)
    
    print("🚀 Starting AVA OLO Dashboard System...")
    print("\nThis will start:")
    print("   📊 Monitoring Dashboard: http://localhost:8080/monitoring_dashboard.html")
    print("   🗃️  Database Explorer:    http://localhost:8080/database_explorer.html")
    print("   🔌 Monitoring API:       http://localhost:8000/docs")
    print("   🔍 Explorer API:         http://localhost:8001/docs")
    
    # Import and run the main dashboard system
    try:
        from run_dashboards import main as run_main
        run_main()
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        print("\nTroubleshooting:")
        print("   • Ensure PostgreSQL is running")
        print("   • Check database credentials in .env")
        print("   • Verify ports 8000, 8001, 8080 are available")

if __name__ == "__main__":
    main()