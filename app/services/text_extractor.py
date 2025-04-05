import re
from typing import Dict, List, Any

def extract_resume_data(text: str) -> Dict[str, Any]:
    """
    Extract structured resume data from plain text using regex patterns
    """
    # Initialize the result dictionary
    resume_data = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "summary": "",
        "skills": [],
        "experience": "",
        "education": ""
    }
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, text)
    if email_matches:
        resume_data["email"] = email_matches[0]
    
    # Extract phone number (various formats)
    phone_pattern = r'(\+\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    phone_matches = re.findall(phone_pattern, text)
    if phone_matches:
        # Join the country code and the main part if present
        phone_parts = [part for part in phone_matches[0] if part]
        resume_data["phone"] = ''.join(phone_parts)
    
    # Extract skills
    skills = extract_skills(text)
    resume_data["skills"] = skills
    
    # Attempt to extract name (usually at the beginning)
    lines = text.strip().split('\n')
    if lines:
        # First non-empty line is often the name
        for line in lines:
            if line.strip() and not re.search(email_pattern, line) and not re.search(phone_pattern, line):
                # Check if the line is likely a name (not too long, no special characters)
                if len(line.strip()) < 50 and re.match(r'^[A-Za-z\s\.\-\']+$', line.strip()):
                    resume_data["name"] = line.strip()
                    break
    
    # Extract education information
    education_section = extract_section(text, ["education", "academic background", "academic", "degree"])
    if education_section:
        resume_data["education"] = education_section
    
    # Extract experience information
    experience_section = extract_section(text, ["experience", "work experience", "employment", "work history"])
    if experience_section:
        resume_data["experience"] = experience_section
    
    # Extract summary if present
    summary_section = extract_section(text, ["summary", "profile", "objective", "about me"])
    if summary_section:
        resume_data["summary"] = summary_section
    
    return resume_data

def extract_section(text: str, section_keywords: List[str]) -> str:
    """Extract a section from the resume text based on keywords"""
    # Create regex pattern to find section (case insensitive)
    pattern = r'(?i)(' + '|'.join(section_keywords) + r')s?[:\s]*(.*?)(?=\n[\s]*\n|\n[\s]*[A-Z][A-Za-z\s]+[:\s]|\Z)'
    
    # Search for the pattern
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(2).strip()
    return ""

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text"""
    # Common tech skills to look for
    common_skills = [
        # Programming Languages
        "Python", "JavaScript", "Java", "C#", "C++", "PHP", "Ruby", "Swift", "Kotlin", "Go", "Rust",
        "TypeScript", "SQL", "HTML", "CSS", "R", "Scala", "Perl", "Shell", "Bash",
        
        # Frameworks and Libraries
        "React", "Angular", "Vue", "Django", "Flask", "Spring", "Express", "Node.js", "ASP.NET",
        "Laravel", "Ruby on Rails", "jQuery", "Bootstrap", "TensorFlow", "PyTorch", "Pandas", 
        "NumPy", "Redux", "Next.js", "Gatsby", "Flutter", "SwiftUI", "Xamarin",
        
        # Databases
        "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle", "SQL Server", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "MariaDB", "Firebase", "Neo4j", "Couchbase",
        
        # Cloud & DevOps
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins", "Git", "GitHub", "GitLab",
        "Terraform", "Ansible", "Puppet", "Chef", "CI/CD", "Serverless", "Microservices", "ECS", "EKS",
        "Lambda", "S3", "EC2", "RDS", "VPC", "Heroku", "DigitalOcean", "Netlify", "Vercel",
        
        # AI & Data Science
        "Machine Learning", "Deep Learning", "AI", "Data Science", "Natural Language Processing",
        "Computer Vision", "Data Analysis", "Statistics", "Big Data", "Data Mining", "Hadoop", "Spark",
        "Airflow", "Data Visualization", "Tableau", "Power BI", "scikit-learn", "Keras",
        
        # Other Common Skills
        "Agile", "Scrum", "RESTful API", "GraphQL", "JSON", "XML", "Linux", "Windows", "macOS",
        "UI/UX", "Responsive Design", "Testing", "Unit Testing", "Selenium", "Jest", "Cypress"
    ]
    
    # Extract skills section if it exists
    skills_section = extract_section(text, ["skills", "technical skills", "technologies", "competencies"])
    
    # Find skills from the common list in the entire text
    matched_skills = []
    for skill in common_skills:
        # Use word boundary to ensure whole word match
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            matched_skills.append(skill)
    
    # If a skills section was found, try to extract additional skills
    if skills_section:
        # Look for bullet points or comma-separated skills
        bullet_skills = re.findall(r'[•\-\*]\s*([^•\-\*\n]+)', skills_section)
        for skill in bullet_skills:
            skill = skill.strip()
            if skill and skill not in matched_skills and len(skill) < 50:  # Avoid long phrases
                matched_skills.append(skill)
        
        # Check for comma-separated skills
        if ',' in skills_section:
            comma_skills = [s.strip() for s in skills_section.split(',')]
            for skill in comma_skills:
                if skill and skill not in matched_skills and len(skill) < 50:
                    matched_skills.append(skill)
    
    return matched_skills