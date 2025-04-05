import importlib
import sys

def check_dependency(name, display_name=None):
    display_name = display_name or name
    try:
        importlib.import_module(name)
        print(f"✓ {display_name} is installed")
        return True
    except ImportError:
        print(f"✗ {display_name} is NOT installed")
        return False

print("\nChecking dependencies for Vibezsume...\n")

dependencies = [
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("pydantic", "Pydantic"),
    ("jinja2", "Jinja2"),
    ("fitz", "PyMuPDF"),
    ("docx", "python-docx"),
    ("spacy", "spaCy"),
    ("sentence_transformers", "Sentence Transformers"),
]

missing = 0
for module, display_name in dependencies:
    if not check_dependency(module, display_name):
        missing += 1

print("\n")
if missing > 0:
    print(f"Missing {missing} dependencies. Please install with:")
    print("pip install -r requirements.txt")
    print("\nFor spaCy models, also run:")
    print("python -m spacy download en_core_web_sm")
else:
    print("All required dependencies are installed!")

# Try to load spaCy model
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    print("✓ spaCy language model 'en_core_web_sm' is installed")
except (ImportError, OSError):
    print("✗ spaCy language model 'en_core_web_sm' is NOT installed")
    print("Install it with: python -m spacy download en_core_web_sm")