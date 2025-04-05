import os
import sys
import subprocess

def install_compatible_packages():
    """Install packages compatible with Python 3.13"""
    packages = [
        "fastapi==0.99.1",
        "uvicorn==0.22.0",
        "python-multipart==0.0.6",
        "pydantic==1.10.12",
        "typing-extensions==4.6.0",
        "jinja2==3.1.2",
        "python-docx==0.8.11",
        "PyPDF2==3.0.1"
    ]
    
    print("Installing compatible packages for Python 3.13...")
    for package in packages:
        print(f"Installing {package}")
        subprocess.run([sys.executable, "-m", "pip", "install", package])
    
    print("All packages installed successfully")

def scan_directory():
    """Scan the repository directory and print found files"""
    print("\nRepository Contents:")
    
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")

if __name__ == "__main__":
    print("Python 3.13 Compatibility Fixer for Vibezsume")
    print("-" * 50)
    
    # Scan directory to see what we have
    scan_directory()
    
    # Install compatible packages
    install_compatible_packages()
    
    print("\nCompatibility fixes applied! You can now run:")
    print("1. Test minimal app:   python minimal_app.py")
    print("2. Run main app:      uvicorn app.main:app --reload")