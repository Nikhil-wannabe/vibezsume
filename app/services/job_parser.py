import re
from typing import Dict, List, Tuple
from collections import Counter

# Try to load spaCy
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    print("Warning: spaCy model not available. Using simplified parsing.")

# Common tech skills to look for
COMMON_TECH_SKILLS = [
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
    "UI/UX", "Responsive Design", "Testing", "Unit Testing", "Selenium", "Jest", "Cypress",
    "Blockchain", "IoT", "Mobile Development", "Web Development", "Full Stack", "Front End",
    "Back End", "System Design", "Object-Oriented Programming", "Functional Programming",
    "API Development", "Security", "Authentication", "OAuth"
]

def extract_job_title(text: str) -> str:
    """Extract the job title from a job description"""
    common_titles = [
        "Software Engineer", "Data Scientist", "DevOps Engineer", "Frontend Developer",
        "Backend Developer", "Full Stack Developer", "Machine Learning Engineer",
        "Data Analyst", "Product Manager", "QA Engineer", "UX Designer", "UI Designer",
        "Cloud Engineer", "System Administrator", "Database Administrator", "Mobile Developer",
        "Android Developer", "iOS Developer", "Web Developer", "Security Engineer"
    ]
    
    # Check the first few lines for a title
    lines = text.split('\n')
    first_lines = ' '.join(lines[:10]).lower()
    
    for title in common_titles:
        if title.lower() in first_lines:
            return title
    
    # Look for patterns like "Job Title: Something"
    title_pattern = re.search(r'(?:job title|position|role|title)\s*(?::|is|as)\s*([^\n\.]+)', 
                               first_lines, re.IGNORECASE)
    if title_pattern:
        return title_pattern.group(1).strip()
    
    # Otherwise, return first line as a fallback
    for line in lines:
        if line.strip():
            # Clean up the line
            clean_line = re.sub(r'[\(\):]', '', line.strip())
            # Truncate if too long
            if len(clean_line) > 50:
                clean_line = clean_line[:50] + "..."
            return clean_line
    
    return "Software Professional"  # default fallback

def extract_skills_from_job(text: str) -> List[str]:
    """Extract skills from job description"""
    if SPACY_AVAILABLE:
        return extract_skills_spacy(text)
    else:
        return extract_skills_keyword(text)

def extract_skills_spacy(text: str) -> List[str]:
    """Extract skills using spaCy NLP"""
    doc = nlp(text)
    
    # Extract noun phrases and named entities as potential skills
    potential_skills = []
    
    # Get noun phrases
    for chunk in doc.noun_chunks:
        potential_skills.append(chunk.text.strip())
    
    # Get named entities
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]:
            potential_skills.append(ent.text.strip())
    
    # Check against common tech skills
    skills = []
    for skill in COMMON_TECH_SKILLS:
        if skill.lower() in text.lower():
            # Check for whole word match
            pattern = r'\b{}\b'.format(re.escape(skill))
            if re.search(pattern, text, re.IGNORECASE):
                skills.append(skill)
    
    # Add phrases that might be skills
    for phrase in potential_skills:
        # Skip if too long or too short
        if len(phrase) < 3 or len(phrase) > 30:
            continue
            
        # Skip common non-skill phrases
        if phrase.lower() in ["we", "you", "they", "i", "he", "she", "it", "our", "your", "their", 
                             "us", "them", "me", "him", "her"]:
            continue
            
        # Check if this might be a skill
        if any(word.lower() in phrase.lower() for word in ["experience", "knowledge", "skill", "proficiency", 
                                                          "familiar", "framework", "language", "platform"]):
            # Extract what might be the actual skill
            skill_match = re.search(r'(?:with|in|of|using)\s+([^,\.]+)', phrase)
            if skill_match:
                candidate = skill_match.group(1).strip()
                # Skip if too long or too short
                if 3 <= len(candidate) <= 30:
                    skills.append(candidate)
    
    # Remove duplicates and sort
    return sorted(list(set(skills)))

def extract_skills_keyword(text: str) -> List[str]:
    """Extract skills using keyword matching"""
    skills = []
    
    # Check for common tech skills
    for skill in COMMON_TECH_SKILLS:
        # Check for whole word match
        pattern = r'\b{}\b'.format(re.escape(skill))
        if re.search(pattern, text, re.IGNORECASE):
            skills.append(skill)
    
    # Look for skill sections
    skill_section = re.search(r'(?:skills|requirements|qualifications)[^\n]*:(.*?)(?:\n\n|\n\s*\n|$)', 
                              text, re.IGNORECASE | re.DOTALL)
    
    if skill_section:
        skill_text = skill_section.group(1)
        
        # Extract skills from bullet points
        bullet_skills = re.findall(r'[•\-\*]\s*([^\n•\-\*]+)', skill_text)
        for skill in bullet_skills:
            skill = skill.strip()
            if 3 <= len(skill) <= 50:  # Reasonable skill length
                skills.append(skill)
    
    # Remove duplicates and sort
    return sorted(list(set(skills)))

def extract_requirements(text: str) -> Tuple[List[str], List[str]]:
    """Extract required and preferred skills from job description"""
    required_skills = []
    preferred_skills = []
    
    # Get all skills first
    all_skills = extract_skills_from_job(text)
    
    # Find required and preferred sections
    required_section = re.search(r'(?:required|requirements|must have)[^\n]*:(.*?)(?:\n\n|\n\s*\n|$|(?:preferred|nice to have|plus))', 
                                text, re.IGNORECASE | re.DOTALL)
    
    preferred_section = re.search(r'(?:preferred|nice to have|plus)[^\n]*:(.*?)(?:\n\n|\n\s*\n|$)', 
                                 text, re.IGNORECASE | re.DOTALL)
    
    # Process required section
    if required_section:
        req_text = required_section.group(1).lower()
        for skill in all_skills:
            if skill.lower() in req_text:
                required_skills.append(skill)
    
    # Process preferred section
    if preferred_section:
        pref_text = preferred_section.group(1).lower()
        for skill in all_skills:
            if skill.lower() in pref_text:
                preferred_skills.append(skill)
    
    # If no explicit sections found, use keyword detection
    if not required_section and not preferred_section:
        for skill in all_skills:
            skill_lower = skill.lower()
            
            # Search for the skill with context
            context_pattern = r'(?:([^\.]*%s[^\.]*))' % re.escape(skill_lower)
            contexts = re.findall(context_pattern, text.lower())
            
            is_required = False
            is_preferred = False
            
            for context in contexts:
                if any(req in context for req in ['required', 'must have', 'must be', 'necessity', 'essential']):
                    is_required = True
                    break
                if any(pref in context for pref in ['preferred', 'nice to have', 'plus', 'advantage', 'beneficial']):
                    is_preferred = True
                    break
            
            if is_required:
                required_skills.append(skill)
            elif is_preferred:
                preferred_skills.append(skill)
            else:
                # Default to required if no context clues
                required_skills.append(skill)
    
    # Make sure there's no overlap
    preferred_skills = [s for s in preferred_skills if s not in required_skills]
    
    return required_skills, preferred_skills

def parse_job_description(text: str) -> Dict:
    """Parse a job description and extract relevant information"""
    job_title = extract_job_title(text)
    required_skills, preferred_skills = extract_requirements(text)
    
    return {
        "job_title": job_title,
        "required_skills": required_skills,
        "nice_to_have": preferred_skills,
        "description": text[:500] + "..." if len(text) > 500 else text  # Truncated description
    }