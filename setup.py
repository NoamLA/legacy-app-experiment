#!/usr/bin/env python3
"""
Quick setup script for Legacy Interview App with virtual environment
"""
import os
import shutil
import subprocess
import sys
import venv

# Virtual environment configuration
VENV_NAME = "legacy-venv"
VENV_PATH = os.path.join(os.getcwd(), VENV_NAME)

def check_file_exists(filepath):
    """Check if a file exists"""
    return os.path.exists(filepath)

def create_venv():
    """Create virtual environment if it doesn't exist"""
    if not os.path.exists(VENV_PATH):
        print(f"📦 Creating virtual environment: {VENV_NAME}")
        try:
            venv.create(VENV_PATH, with_pip=True)
            print(f"✅ Virtual environment created at {VENV_PATH}")
            return True
        except Exception as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    else:
        print(f"✅ Virtual environment already exists: {VENV_NAME}")
        return True

def get_venv_python():
    """Get the path to Python in the virtual environment"""
    if sys.platform == "win32":
        return os.path.join(VENV_PATH, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_PATH, "bin", "python")

def get_venv_pip():
    """Get the path to pip in the virtual environment"""
    if sys.platform == "win32":
        return os.path.join(VENV_PATH, "Scripts", "pip.exe")
    else:
        return os.path.join(VENV_PATH, "bin", "pip")

def install_python_deps():
    """Install Python dependencies in virtual environment"""
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    pip_path = get_venv_pip()
    if not os.path.exists(pip_path):
        print("❌ Virtual environment pip not found")
        return False
    
    print("📦 Installing Python dependencies in virtual environment...")
    try:
        result = subprocess.run([
            pip_path, "install", "-r", "requirements.txt"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Python dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install Python dependencies: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def copy_env_template():
    """Copy environment template to .env if it doesn't exist"""
    if not check_file_exists('.env'):
        if check_file_exists('.env.template'):
            shutil.copy('.env.template', '.env')
            print("✅ Created .env from template")
            return True
        else:
            print("❌ .env.template not found")
            return False
    else:
        print("ℹ️  .env already exists")
        return True

def check_python_deps():
    """Check if Python dependencies are installed in virtual environment"""
    python_path = get_venv_python()
    if not os.path.exists(python_path):
        print("❌ Virtual environment Python not found")
        return False
    
    try:
        # Test imports using the virtual environment Python
        result = subprocess.run([
            python_path, "-c", 
            "import agno, fastapi, uvicorn; print('All dependencies available')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Python dependencies are installed in virtual environment")
            return True
        else:
            print("❌ Missing Python dependencies in virtual environment")
            print("Dependencies will be installed automatically...")
            return install_python_deps()
    except Exception as e:
        print(f"❌ Error checking Python dependencies: {e}")
        return False

def check_node_deps():
    """Check if Node.js dependencies are installed"""
    if check_file_exists('node_modules'):
        print("✅ Node.js dependencies are installed")
        return True
    else:
        print("❌ Node.js dependencies not found")
        print("Run: npm install")
        return False

def check_api_key():
    """Check if OpenAI API key is configured"""
    python_path = get_venv_python()
    
    try:
        # Use virtual environment Python to check API key
        result = subprocess.run([
            python_path, "-c", 
            """
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if api_key and api_key != 'your_openai_api_key_here':
    print('configured')
else:
    print('missing')
            """
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'configured' in result.stdout:
            print("✅ OpenAI API key is configured")
            return True
        else:
            print("❌ OpenAI API key not configured")
            print("Edit .env file and add your OpenAI API key")
            return False
    except Exception as e:
        print(f"❌ Error checking API key: {e}")
        return False

def main():
    print("🚀 Legacy Interview App - Virtual Environment Setup")
    print("=" * 60)
    
    all_good = True
    
    # Create virtual environment
    if not create_venv():
        all_good = False
    
    # Check environment setup
    if not copy_env_template():
        all_good = False
    
    # Check Python dependencies (will install if missing)
    if not check_python_deps():
        all_good = False
    
    # Check Node.js dependencies
    if not check_node_deps():
        all_good = False
    
    # Check API key (only if .env exists)
    if check_file_exists('.env'):
        try:
            if not check_api_key():
                all_good = False
        except Exception as e:
            print(f"⚠️  Could not check API key: {e}")
    
    print("=" * 60)
    
    if all_good:
        print("🎉 Setup complete! You can now run:")
        print(f"   Activate venv: source {VENV_NAME}/bin/activate  (Linux/Mac)")
        print(f"                  {VENV_NAME}\\Scripts\\activate     (Windows)")
        print("   Backend:       python start-backend.py")
        print("   Frontend:      ./start-frontend.sh")
        print("   Then visit:    http://localhost:3000")
        print()
        print("💡 Or use the activation scripts:")
        print("   ./start-with-venv.sh  (starts backend with venv)")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        print("📚 See SETUP.md and env-setup.md for detailed instructions.")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
