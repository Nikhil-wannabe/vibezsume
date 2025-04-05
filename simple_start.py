import os
import sys
import re

def check_python_files():
    """Check all Python files for comment syntax issues"""
    fixed_files = 0
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Check for // comments and fix them
                    if "// filepath:" in content:
                        print(f"Fixing comment syntax in {path}")
                        content = content.replace("// filepath:", "# filepath:")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(content)
                        fixed_files += 1
                except Exception as e:
                    print(f"Error processing {path}: {str(e)}")
    
    if fixed_files > 0:
        print(f"Fixed comment syntax in {fixed_files} files")
    else:
        print("No files needed fixing")

def create_minimal_requirements():
    """Create a minimal_requirements.txt file if it doesn't exist"""
    if not os.path.exists("minimal_requirements.txt"):
        print("Creating minimal_requirements.txt")
        with open("minimal_requirements.txt", "w") as f:
            f.write("""fastapi==0.95.1
uvicorn==0.22.0
python-multipart==0.0.6
pydantic==1.10.7
jinja2==3.1.2
python-docx==0.8.11
PyPDF2==2.11.2
beautifulsoup4==4.11.1
requests==2.28.1
""")
        print("minimal_requirements.txt created")
    else:
        print("minimal_requirements.txt already exists")

def create_python313_requirements():
    """Create a Python 3.13 compatible requirements.txt file"""
    req_file = "py313_requirements.txt"
    if not os.path.exists(req_file):
        print(f"Creating {req_file}")
        with open(req_file, "w") as f:
            f.write("""fastapi==0.99.1
uvicorn==0.22.0
python-multipart==0.0.6
pydantic==1.10.12
typing-extensions==4.6.0
jinja2==3.1.2
python-docx==0.8.11
PyPDF2==3.0.1
""")
        print(f"{req_file} created")
    else:
        print(f"{req_file} already exists")

def ensure_directory_structure():
    """Ensure all necessary directories exist"""
    directories = [
        'app',
        'app/data',
        'app/models',
        'app/routers',
        'app/services',
        'uploads'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)
            
            # Create __init__.py in Python package directories
            if directory.startswith('app'):
                init_file = os.path.join(directory, '__init__.py')
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        f.write('# This file makes the directory a Python package\n')
                    print(f"Created {init_file}")

def check_minimal_app():
    """Create a minimal app.py file to test FastAPI"""
    app_path = "minimal_app.py"
    if not os.path.exists(app_path):
        print(f"Creating minimal FastAPI app for testing")
        with open(app_path, "w") as f:
            f.write("""
# A minimal FastAPI app to test functionality
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("minimal_app:app", host="0.0.0.0", port=8000, reload=True)
""")
        print(f"Created {app_path}")
    else:
        print(f"{app_path} already exists")

if __name__ == "__main__":
    print("Setting up Vibezsume for Python 3.13...")
    
    # Step 1: Ensure directory structure
    print("\n1. Checking directory structure...")
    ensure_directory_structure()
    
    # Step 2: Fix comment syntax in Python files
    print("\n2. Checking Python files for syntax issues...")
    check_python_files()
    
    # Step 3: Create Python 3.13 compatible requirements file
    print("\n3. Setting up Python 3.13 compatible requirements...")
    create_python313_requirements()
    
    # Step 4: Create minimal app for testing
    print("\n4. Creating minimal test app...")
    check_minimal_app()
    
    # Step 5: Install dependencies
    print("\n5. Installing Python 3.13 compatible dependencies...")
    os.system(f"{sys.executable} -m pip install -r py313_requirements.txt")
    
    # Step 6: Test with minimal app first
    print("\n6. Testing with minimal app first...")
    print("Starting minimal test app. Press Ctrl+C to stop and continue to main app...")
    os.system(f"{sys.executable} minimal_app.py")
    
    # Step 7: Start the main app if minimal test was successful
    print("\n7. Starting Vibezsume main app...")
    os.system(f"{sys.executable} -m uvicorn app.main:app --reload")