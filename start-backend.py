#!/usr/bin/env python3
"""
Start script for the Legacy Interview App backend
"""
import os
import sys
import subprocess

def check_requirements():
    """Check if required packages are installed"""
    try:
        import agno
        import fastapi
        import uvicorn
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def main():
    print("🚀 Starting Legacy Interview App Backend...")
    
    if not check_requirements():
        sys.exit(1)
    
    # Set environment variables
    os.environ.setdefault('AGNO_TELEMETRY', 'false')
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    # Start the FastAPI server
    print("📡 Starting FastAPI server on http://localhost:8000")
    print("📖 API docs will be available at http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0', 
            '--port', '8000', 
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped")

if __name__ == "__main__":
    main()
