#!/usr/bin/env python3
"""
Setup script for Employee Engagement Pulse
Helps initialize the environment, database, and generate sample data
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                Employee Engagement Pulse                     ║
║            🚀 Setup and Initialization Script               ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_env_file():
    """Check if .env file exists and help create it"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📄 Creating .env file from .env.example...")
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ .env file created")
            print("⚠️  Please edit .env file with your actual Slack credentials")
            return False
        else:
            print("❌ Error: .env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
        return True

def install_python_deps():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Python dependencies: {e}")
        return False

def install_node_deps():
    """Install Node.js dependencies for frontend"""
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("⚠️  Frontend directory not found, skipping Node.js setup")
        return True
    
    print("📦 Installing Node.js dependencies...")
    try:
        subprocess.check_call(["npm", "install"], cwd=frontend_dir)
        print("✅ Node.js dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Node.js dependencies: {e}")
        return False
    except FileNotFoundError:
        print("⚠️  npm not found. Please install Node.js to set up the frontend")
        return False

def setup_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    try:
        # Import and initialize the database
        from app.models import init_db
        init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def generate_sample_data():
    """Generate sample Slack data for testing"""
    print("🎭 Generating sample data...")
    try:
        # Run the seeding script
        seed_script = Path("app/seeds/seed_fake_slack.py")
        subprocess.check_call([
            sys.executable, str(seed_script),
            "--channels", "general", "backend", "frontend", "random",
            "--users", "15",
            "--messages", "500",
            "--days", "30",
            "--personas", "dev,qa,manager,designer"
        ])
        print("✅ Sample data generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating sample data: {e}")
        return False

def run_aggregation():
    """Run initial data aggregation"""
    print("📊 Running initial data aggregation...")
    try:
        from app.aggregator import run_daily_aggregation_job, run_weekly_aggregation_job
        run_daily_aggregation_job()
        run_weekly_aggregation_job()
        print("✅ Initial aggregation completed")
        return True
    except Exception as e:
        print(f"❌ Error running aggregation: {e}")
        return False

def generate_insights():
    """Generate initial insights"""
    print("💡 Generating initial insights...")
    try:
        from app.insights import run_insight_generation_job
        run_insight_generation_job()
        print("✅ Initial insights generated")
        return True
    except Exception as e:
        print(f"❌ Error generating insights: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🎉 Setup Complete!                       ║
╚══════════════════════════════════════════════════════════════╝

Next steps:

1️⃣  Start the backend API:
   uvicorn app.main:app --reload

2️⃣  Start the frontend (in a new terminal):
   cd frontend
   npm start

3️⃣  Open your browser to:
   http://localhost:3000

4️⃣  For Slack integration:
   - Configure your .env file with real Slack credentials
   - Set up Slack App with Events API
   - Point Slack webhook to http://yourserver:8000/slack/events

📚 Useful commands:

• Generate more test data:
  python app/seeds/seed_fake_slack.py --help

• Run aggregation manually:
  python -c "from app.aggregator import *; run_daily_aggregation_job()"

• Check system status:
  curl http://localhost:8000/health

• View API docs:
  http://localhost:8000/docs

Happy analyzing! 🚀
    """)

def main():
    parser = argparse.ArgumentParser(description="Setup Employee Engagement Pulse")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-data", action="store_true", help="Skip sample data generation")
    parser.add_argument("--docker", action="store_true", help="Set up for Docker environment")
    args = parser.parse_args()

    print_banner()
    
    # Basic checks
    check_python_version()
    
    # Environment setup
    env_ready = check_env_file()
    
    # Dependency installation
    if not args.skip_deps:
        if not install_python_deps():
            print("⚠️  Python dependency installation failed, continuing anyway...")
        
        if not args.docker:
            if not install_node_deps():
                print("⚠️  Node.js dependency installation failed, continuing anyway...")
    
    # Database setup
    if not setup_database():
        print("❌ Database setup failed. Please check your DATABASE_URL in .env")
        sys.exit(1)
    
    # Sample data generation
    if not args.skip_data:
        if generate_sample_data():
            print("📊 Processing sample data...")
            run_aggregation()
            generate_insights()
        else:
            print("⚠️  Sample data generation failed, but setup can continue")
    
    print_next_steps()

if __name__ == "__main__":
    main()
