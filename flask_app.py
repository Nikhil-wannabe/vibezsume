from flask import Flask, render_template, send_from_directory, jsonify, request
import os
from pathlib import Path

app = Flask(__name__)

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent

# Set up static file serving
@app.route('/styles.css')
def css():
    return send_from_directory(BASE_DIR, 'styles.css')

@app.route('/script.js')
def js():
    return send_from_directory(BASE_DIR, 'script.js')

@app.route('/')
def index():
    # Try to serve index.html from the root directory
    index_path = BASE_DIR / 'index.html'
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return """
        <html>
            <head>
                <title>Vibezsume</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    h1 { color: #333; }
                </style>
            </head>
            <body>
                <h1>Vibezsume</h1>
                <p>Welcome to Vibezsume - Resume Analysis and Builder</p>
                <p>The index.html file was not found in the root directory.</p>
            </body>
        </html>
        """

@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Vibezsume API is running with Flask"})

# Mock API endpoints
@app.route('/resume/upload', methods=['POST'])
def upload_resume():
    return jsonify({
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-123-4567",
        "skills": ["Python", "JavaScript", "React", "HTML", "CSS"],
        "education": "Bachelor's in Computer Science",
        "experience": "5 years software development experience",
        "summary": "Experienced software developer with strong web development skills"
    })

@app.route('/resume/job-description', methods=['POST'])
def analyze_job():
    return jsonify({
        "id": "job123",
        "job_title": "Frontend Developer",
        "required_skills": ["JavaScript", "HTML", "CSS", "React"],
        "nice_to_have": ["TypeScript", "Redux", "UI/UX"],
        "description_preview": "We are looking for a Frontend Developer with experience in React..."
    })

@app.route('/resume/match-jobs', methods=['POST'])
def match_jobs():
    return jsonify([{
        "job_title": "Frontend Developer",
        "match_score": 75.5,
        "match_strength": "Good match",
        "matched_required_skills": ["JavaScript", "HTML", "CSS"],
        "matched_nice_to_have": ["Redux"],
        "missing_required_skills": ["React"],
        "recommendations": ["Add React to your skills", "Include more frontend project examples"],
        "job_description": "We are looking for a Frontend Developer with experience in React..."
    }])

if __name__ == '__main__':
    # Create an uploads directory if it doesn't exist
    uploads_dir = BASE_DIR / 'uploads'
    if not uploads_dir.exists():
        os.makedirs(uploads_dir)
        print(f"Created uploads directory at {uploads_dir}")
    
    # Print repository content
    print("Repository contents:")
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root) or '.'}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{sub_indent}{f}")
    
    # Start the Flask server
    print("\nStarting Vibezsume with Flask instead of FastAPI")
    print("Visit http://localhost:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=True)