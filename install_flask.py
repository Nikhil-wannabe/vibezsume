import subprocess
import sys

def install_flask():
    """Install Flask as a simpler alternative to FastAPI"""
    print("Installing Flask and related packages...")
    
    packages = [
        "flask",
        "python-docx==0.8.11",
        "PyPDF2==3.0.1"
    ]
    
    for package in packages:
        print(f"Installing {package}")
        subprocess.run([sys.executable, "-m", "pip", "install", package])
    
    print("All packages installed successfully")

if __name__ == "__main__":
    install_flask()
    print("\nFlask has been installed. You can now run:")
    print("python flask_app.py")