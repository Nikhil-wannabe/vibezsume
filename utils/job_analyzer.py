import spacy
import re

# Load the small English model for spacy
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("Spacy model 'en_core_web_sm' not found. Please download it: python -m spacy download en_core_web_sm")
    nlp = spacy.blank("en") # Fallback, NER will be limited

# Predefined skills list (can be expanded significantly or loaded from a file)
SKILLS_LIST = [
    # Programming Languages
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'go', 'rust', 'sql', 'nosql',
    # Web Technologies & Frameworks
    'html', 'css', 'react', 'angular', 'vue', 'vue.js' 'node.js', 'jquery', 'django', 'flask', 'spring', 'spring boot', '.net', 'asp.net',
    'ruby on rails', 'laravel', 'express.js',
    # Databases
    'mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'cassandra', 'elasticsearch', 'oracle', 'sql server',
    # Cloud Platforms & DevOps
    'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'k8s', 'openshift', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'git', 'svn',
    'linux', 'unix', 'bash', 'powershell',
    # Data Science & Machine Learning
    'machine learning', 'deep learning', 'nlp', 'natural language processing', 'computer vision', 'data analysis',
    'data science', 'pandas', 'numpy', 'scipy', 'scikit-learn', 'sklearn', 'tensorflow', 'keras', 'pytorch', 'spark', 'hadoop',
    'r programming', 'tableau', 'power bi',
    # Software Development & Methodologies
    'agile', 'scrum', 'kanban', 'waterfall', 'devops', 'rest', 'soap', 'apis', 'microservices', 'tdd', 'bdd', 'unit testing',
    'integration testing', 'software architecture', 'design patterns',
    # Business & Soft Skills (examples)
    'communication', 'teamwork', 'problem solving', 'leadership', 'project management', 'product management',
    'analytical skills', 'critical thinking', 'creativity', 'time management', 'customer service', 'sales', 'marketing',
    'stakeholder management', 'negotiation', 'presentation skills',
    # Other Specific Tools/Technologies
    'sap', 'salesforce', 'sharepoint', 'jira', 'confluence', 'slack', 'microsoft office', 'excel', 'word', 'powerpoint'
]


def extract_skills_from_text(text_lower):
    """Extracts skills from text based on a predefined list."""
    found_skills = set()
    # Using regex to find whole word matches for skills, especially multi-word ones
    for skill in SKILLS_LIST:
        # Create a regex pattern for the skill, handling special characters like C++ or C#
        # \b ensures word boundaries. re.escape handles special chars in skill names.
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Use a consistent capitalization for display if desired, or the original from SKILLS_LIST
            # For now, let's use the version from SKILLS_LIST which is mostly lowercase
            # but could be capitalized if the list was defined that way.
            # For consistency with resume parser, let's capitalize.
            found_skills.add(skill.capitalize() if not skill.isupper() else skill)
    return sorted(list(found_skills))

def extract_experience_level(text):
    """Extracts years of experience and seniority levels."""
    years_experience = None
    seniority = None

    # Regex for years of experience (e.g., "5+ years", "3-5 years", "at least 2 years")
    # This pattern is quite broad and might pick up other numbers.
    # Adding keywords like "experience" or "proven track record" nearby could refine it.
    exp_pattern = re.compile(
        r'(\d{1,2}\s*(?:to|-|–|—)\s*\d{1,2}|\d{1,2}\s*\+|\+\s*\d{1,2}|at least\s+\d{1,2}|minimum\s+\d{1,2})\s+years?(?:\s+of)?\s+(?:relevant\s+)?(?:work\s+)?experience',
        re.IGNORECASE
    )
    match = exp_pattern.search(text)
    if match:
        years_experience = match.group(1).strip()
        # Normalize: "5 +" to "5+", "at least 2" to "2+"
        if 'to' in years_experience or '-' in years_experience or '–' in years_experience or '—' in years_experience :
            pass # Keep as range e.g. 3-5
        elif '+' in years_experience:
            years_experience = years_experience.replace(' ', '')
        elif 'at least' in years_experience.lower() or 'minimum' in years_experience.lower():
            num_match = re.search(r'\d{1,2}', years_experience)
            if num_match:
                years_experience = num_match.group(0) + "+"

    # Keywords for seniority
    seniority_keywords = {
        'Senior': [r'senior', r'sr\.', r'lead'], # Added 'lead'
        'Junior': [r'junior', r'jr\.', r'entry-level', r'graduate'], # Added 'graduate'
        'Mid-Level': [r'mid-level', r'intermediate'],
        'Principal': [r'principal'],
        'Staff': [r'staff engineer', r'staff software'], # More specific for staff
        'Manager': [r'manager', r'manage'] # Broad, could be project manager etc.
    }
    text_lower = text.lower()
    found_seniorities = set()
    for level, keywords in seniority_keywords.items():
        for kw in keywords:
            if re.search(r'\b' + kw + r'\b', text_lower):
                found_seniorities.add(level)

    # Prioritize if multiple are found (e.g., "Senior Manager" -> Manager, or "Senior" if "Lead" also found)
    if 'Manager' in found_seniorities: seniority = 'Manager'
    elif 'Principal' in found_seniorities: seniority = 'Principal'
    elif 'Staff' in found_seniorities: seniority = 'Staff'
    elif 'Lead' in found_seniorities and 'Senior' in found_seniorities: seniority = 'Lead/Senior' # Or just Lead
    elif 'Senior' in found_seniorities: seniority = 'Senior'
    elif 'Mid-Level' in found_seniorities: seniority = 'Mid-Level'
    elif 'Junior' in found_seniorities: seniority = 'Junior'

    return years_experience, seniority


def extract_company_name_basic(doc):
    """Very basic company name extraction using NER (ORG entities)."""
    # This is highly unreliable from just a job description text alone,
    # as "ORG" could be many things (clients, partners, technologies).
    # A better approach would be if the source of the scrape (e.g. URL pattern) implies the company.
    # For now, we'll look for ORG entities that are mentioned frequently or near "About"

    # Simple heuristic: look for "About [ORG]"
    about_match = re.search(r"About\s+([A-Z][\w\s.&'-]+)\n", doc.text, re.IGNORECASE)
    if about_match:
        return about_match.group(1).strip()

    # Fallback: Most frequent ORG entity (still not very reliable)
    orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
    if orgs:
        # Filter out very common words that might be misclassified as ORGs
        common_org_noise = {'Inc', 'Ltd', 'Company', 'Corporation', 'Group', 'Solutions', 'Technologies'}
        orgs = [org for org in orgs if org not in common_org_noise and len(org)>2]
        if orgs:
            from collections import Counter
            org_counts = Counter(orgs)
            return org_counts.most_common(1)[0][0]
    return None


def analyze_job_text(text: str) -> dict:
    """
    Analyzes job description text to extract skills, experience, etc.
    """
    if not text:
        return {
            'skills': ["N/A"],
            'experience_years': "N/A",
            'seniority': "N/A",
            'company_name': "N/A"
        }

    doc = nlp(text)
    text_lower = text.lower() # For case-insensitive keyword searches

    skills = extract_skills_from_text(text_lower)
    years_experience, seniority = extract_experience_level(text) # Use full text for context
    company_name = extract_company_name_basic(doc) # Basic attempt

    return {
        'skills': skills if skills else ["N/A"],
        'experience_years': years_experience if years_experience else "N/A",
        'seniority': seniority if seniority else "N/A",
        'company_name': company_name if company_name else "N/A"
    }

if __name__ == '__main__':
    sample_job_description = """
    Senior Software Engineer - Backend
    ExampleCorp - San Francisco, CA

    About ExampleCorp
    ExampleCorp is a leading innovator in the tech industry, dedicated to creating solutions that change the world.

    We are looking for a Senior Software Engineer with 5+ years of experience in backend development.
    The ideal candidate will have a strong background in Python, Java, and cloud platforms like AWS or GCP.
    Experience with microservices architecture, Docker, and Kubernetes is a big plus.
    You should be proficient in SQL and NoSQL databases, such as PostgreSQL and MongoDB.
    Responsibilities include designing, developing, and deploying scalable backend services.
    Must have excellent communication and problem-solving skills.
    A Bachelor's degree in Computer Science or related field is required. M.S. preferred.
    This is a full-time position. We are also hiring for a Junior Developer role.
    Relevant experience: 3-5 years of professional software development.
    """

    print("--- Analyzing Sample Job Description ---")
    analysis_results = analyze_job_text(sample_job_description)

    import json
    print(json.dumps(analysis_results, indent=2))

    another_jd = """
    Data Scientist
    DataDriven Inc.
    We need a data scientist with at least 3 years of experience in machine learning and data analysis.
    Skills: Python, R Programming, Pandas, Scikit-learn, TensorFlow.
    SQL knowledge is essential. Join our team!
    """
    print("\n--- Analyzing Another Job Description ---")
    analysis_results_2 = analyze_job_text(another_jd)
    print(json.dumps(analysis_results_2, indent=2))

    minimal_jd = "Software Engineer. Python, Java. 2+ years experience."
    print("\n--- Analyzing Minimal Job Description ---")
    analysis_results_3 = analyze_job_text(minimal_jd)
    print(json.dumps(analysis_results_3, indent=2))

    no_info_jd = ""
    print("\n--- Analyzing Empty Job Description ---")
    analysis_results_4 = analyze_job_text(no_info_jd)
    print(json.dumps(analysis_results_4, indent=2))
    pass
