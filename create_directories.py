import os

# Create necessary directories
directories = [
    'app',
    'app/data',
    'app/models',
    'app/routers',
    'app/services',
    'uploads'  # For temporarily storing uploaded files
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

# Create empty __init__.py files where needed
init_files = [
    'app/__init__.py',
    'app/models/__init__.py',
    'app/routers/__init__.py',
    'app/services/__init__.py'
]

for init_file in init_files:
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# This file makes the directory a Python package\n')
        print(f"Created file: {init_file}")

print("Directory structure setup complete!")