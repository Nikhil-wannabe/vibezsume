@echo off
REM filepath: c:\Users\nkris\OneDrive\Documents\GitHub\vibezsume\fix_py313.bat
echo Fixing Python 3.13 compatibility issues for Vibezsume...
echo.

echo 1. Creating py313_requirements.txt...
echo fastapi==0.99.1 > py313_requirements.txt
echo uvicorn==0.22.0 >> py313_requirements.txt
echo python-multipart==0.0.6 >> py313_requirements.txt
echo pydantic==1.10.12 >> py313_requirements.txt
echo typing-extensions==4.6.0 >> py313_requirements.txt
echo jinja2==3.1.2 >> py313_requirements.txt
echo python-docx==0.8.11 >> py313_requirements.txt
echo PyPDF2==3.0.1 >> py313_requirements.txt

echo 2. Installing compatible dependencies...
pip install -r py313_requirements.txt

echo 3. Creating minimal test app...
(
echo # A minimal FastAPI app to test functionality
echo from fastapi import FastAPI
echo.
echo app = FastAPI^(^)
echo.
echo @app.get^("/")
echo async def root^(^):
echo     return {"message": "Hello World"}
echo.
echo if __name__ == "__main__":
echo     import uvicorn
echo     uvicorn.run^("minimal_app:app", host="0.0.0.0", port=8000, reload=True^)
) > minimal_app.py

echo 4. Testing minimal app...
echo Press Ctrl+C after confirming it works, then restart the batch file to run the main app.
python minimal_app.py

echo 5. Starting main app...
uvicorn app.main:app --reload

pause