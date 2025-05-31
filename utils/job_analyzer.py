import spacy
import re
from collections import Counter

# --- Constants and Pre-compiled Regex ---
# Regex for experience should be specific to avoid capturing general numbers.
# Using lookarounds or context words like "experience" is crucial.
EXPERIENCE_YEARS_PATTERN = re.compile(
    r'(\b(?:(?:[2-9]|[1-9]\d)\s*(?:to|-|–|—)\s*(?:[2-9]|[1-9]\d)|(?:[2-9]|[1-9]\d)\s*\+|[1-9]\d*\+?\b|at least\s+\d{1,2}|minimum\s+\d{1,2}|(?:a|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:to\s+(?:five|six|seven|eight|nine|ten|eleven|twelve))?)\s+years?(?:\s+of)?\s+(?:relevant\s+)?(?:work\s+)?(?:professional\s+)?experience)',
    re.IGNORECASE
)
# Simplified number extraction from the above, or for general number mentions near "years"
YEAR_NUMBER_PATTERN = re.compile(r'(\d{1,2})')

# For company name extraction
ABOUT_COMPANY_PATTERN = re.compile(r"About\s+([A-Z][\w\s.&'-]+)\n", re.IGNORECASE)


# --- spaCy Model Loading ---
try:
    nlp = spacy.load('en_core_web_sm')
    print("spaCy model 'en_core_web_sm' loaded successfully for job_analyzer.")
except OSError:
    print("job_analyzer.py: spaCy model 'en_core_web_sm' not found. Please download it via: python -m spacy download en_core_web_sm")
    nlp = spacy.blank("en") # Fallback, NER will be limited


# --- Skill Definitions ---
# Moving SKILLS_LIST to a global constant for clarity and potential external loading in future.
# This list should be comprehensive and regularly updated.
# Categories can be added later if needed by making it a dict of lists.
SKILLS_LIST = sorted(list(set([ # Sorted and unique
    # Programming Languages
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'go', 'rust', 'sql', 'nosql', 'pl/sql', 'perl',
    # Web Technologies & Frameworks
    'html', 'css', 'react', 'angular', 'vue', 'vue.js', 'node.js', 'jquery', 'django', 'flask', 'spring', 'spring boot', '.net', 'asp.net',
    'ruby on rails', 'laravel', 'express.js', 'bootstrap', 'tailwind css', 'sass', 'less', 'graphql', 'restful apis', 'soap apis',
    # Databases
    'mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'cassandra', 'elasticsearch', 'oracle', 'sql server', 'mariadb', 'dynamodb',
    # Cloud Platforms & DevOps
    'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'k8s', 'openshift', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'git', 'github', 'gitlab', 'bitbucket', 'svn',
    'linux', 'unix', 'bash scripting', 'powershell', 'serverless', 'aws lambda', 'azure functions',
    # Data Science & Machine Learning
    'machine learning', 'deep learning', 'nlp', 'natural language processing', 'computer vision', 'data analysis', 'data visualization',
    'data science', 'pandas', 'numpy', 'scipy', 'scikit-learn', 'sklearn', 'tensorflow', 'keras', 'pytorch', 'spark', 'apache spark', 'hadoop',
    'r', 'r programming', 'tableau', 'power bi', 'sas', 'matlab', 'statistics', 'econometrics',
    # Software Development & Methodologies
    'agile', 'scrum', 'kanban', 'waterfall', 'devops principles', 'rest', 'soap', 'apis', 'microservices', 'tdd', 'bdd', 'unit testing',
    'integration testing', 'software architecture', 'solution architecture', 'design patterns', 'system design',
    # Business & Soft Skills
    'communication skills', 'teamwork', 'problem-solving skills', 'leadership skills', 'project management', 'product management',
    'analytical skills', 'critical thinking', 'creativity', 'time management skills', 'customer service', 'sales skills', 'marketing strategy',
    'stakeholder management', 'negotiation skills', 'presentation skills', 'technical writing',
    # Other Specific Tools/Technologies
    'sap', 'salesforce', 'sharepoint', 'jira', 'confluence', 'slack', 'microsoft office suite', 'excel', 'ms word', 'ms powerpoint', 'autocad', 'photoshop', 'illustrator'
])))


# --- Extraction Functions ---
def extract_skills_from_text(text_lower: str) -> list[str]:
    """
    Extracts skills from lowercased text based on a predefined list using regex for whole word matching.
    Args:
        text_lower: The lowercased text of the job description.
    Returns:
        A sorted list of unique skills found, capitalized for display.
    """
    found_skills = set()
    for skill in SKILLS_LIST:
        try:
            # Using word boundaries (\b) to match whole words and re.escape for special chars.
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower): # Search in the already lowercased text
                # Capitalize first letter of each word for display if skill is not an acronym like 'AWS'
                if skill.isupper() or skill.islower(): # Simple check for acronyms or single lowercase words
                     found_skills.add(skill.upper() if skill.isupper() else skill.capitalize())
                else: # For skills like 'C++', 'Node.js'
                     found_skills.add(skill)
        except re.error as e:
            print(f"Regex error for skill '{skill}': {e}") # Log regex compilation issues if any
            continue
    return sorted(list(found_skills))

def extract_experience_level(text: str) -> tuple[str | None, str | None]:
    """
    Extracts years of experience and seniority levels from the job description text.
    Args:
        text: The job description text.
    Returns:
        A tuple containing (years_experience_str, seniority_str), or (None, None).
    """
    years_experience_str = None
    seniority_str = None

    # Extract years of experience
    match = EXPERIENCE_YEARS_PATTERN.search(text)
    if match:
        extracted_phrase = match.group(1).strip().lower()
        # Normalize common phrases
        if 'to' in extracted_phrase or '-' in extracted_phrase or '–' in extracted_phrase or '—' in extracted_phrase:
            # For ranges like "3-5 years" or "3 to 5 years"
            numbers = YEAR_NUMBER_PATTERN.findall(extracted_phrase)
            if len(numbers) >= 2:
                years_experience_str = f"{numbers[0]}-{numbers[1]} years"
            elif numbers: # e.g. "up to 5 years" might only match 5
                 years_experience_str = f"Up to {numbers[0]} years"
        elif '+' in extracted_phrase:
            num_match = YEAR_NUMBER_PATTERN.search(extracted_phrase)
            if num_match: years_experience_str = f"{num_match.group(0)}+ years"
        elif 'at least' in extracted_phrase or 'minimum' in extracted_phrase:
            num_match = YEAR_NUMBER_PATTERN.search(extracted_phrase)
            if num_match: years_experience_str = f"{num_match.group(0)}+ years"
        elif YEAR_NUMBER_PATTERN.search(extracted_phrase): # Single number like "5 years experience"
            num_match = YEAR_NUMBER_PATTERN.search(extracted_phrase)
            if num_match: years_experience_str = f"{num_match.group(0)} years"
        else: # Fallback to the matched group if specific parsing fails
            years_experience_str = extracted_phrase + " years"


    # Keywords for seniority
    # Using a dictionary for easier management and explicit boundary matching.
    seniority_keywords_map = {
        'Senior': [r'\bsenior\b', r'\bsr\.?\b'],
        'Lead': [r'\blead\b', r'\bteam lead\b'],
        'Junior': [r'\bjunior\b', r'\bjr\.?\b', r'\bentry-level\b', r'\bgraduate\b'],
        'Mid-Level': [r'\bmid-level\b', r'\bintermediate\b'],
        'Principal': [r'\bprincipal\b'],
        'Staff': [r'\bstaff engineer\b', r'\bstaff software\b', r'\bstaff level\b'],
        'Manager': [r'\bmanager\b', r'\bmanaging\b'] # Be cautious with 'manage'
    }
    text_lower = text.lower()
    found_seniorities = set()
    for level, patterns in seniority_keywords_map.items():
        for pattern_str in patterns:
            if re.search(pattern_str, text_lower):
                found_seniorities.add(level)

    # Prioritization logic for seniority
    if 'Manager' in found_seniorities: seniority_str = 'Manager'
    elif 'Principal' in found_seniorities: seniority_str = 'Principal'
    elif 'Staff' in found_seniorities: seniority_str = 'Staff'
    elif 'Lead' in found_seniorities: seniority_str = 'Lead' # Lead can take precedence over Senior if both found
    elif 'Senior' in found_seniorities: seniority_str = 'Senior'
    elif 'Mid-Level' in found_seniorities: seniority_str = 'Mid-Level'
    elif 'Junior' in found_seniorities: seniority_str = 'Junior'

    return years_experience_str, seniority_str

def extract_company_name_basic(doc: spacy.tokens.Doc) -> str | None:
    """
    Very basic company name extraction using NER (ORG entities) and "About" section heuristic.
    Args:
        doc: spaCy Doc object of the job description text.
    Returns:
        A potential company name string, or None.
    """
    try:
        # Heuristic 1: Look for "About [Company Name]"
        about_match = ABOUT_COMPANY_PATTERN.search(doc.text)
        if about_match:
            return about_match.group(1).strip()

        # Heuristic 2: Most frequent ORG entity, with filtering
        orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
        if orgs:
            common_org_noise = {'Inc', 'Ltd', 'LLC', 'Company', 'Corporation', 'Group', 'Solutions', 'Technologies', 'Systems'}
            # Filter out short orgs and common noise words, unless the org name itself is short (e.g. "SAP")
            filtered_orgs = [org for org in orgs if (len(org) > 2 and org not in common_org_noise) or len(org) <=2 and org in SKILLS_LIST] # keep short if it's a known tech

            if filtered_orgs:
                org_counts = Counter(filtered_orgs)
                # Avoid company names that are also primary skills (e.g. "Python" if misclassified as ORG)
                # unless it's the only ORG found.
                for org_name, count in org_counts.most_common():
                    if org_name.lower() not in SKILLS_LIST or len(org_counts) == 1:
                        return org_name
    except Exception as e:
        print(f"Error in extract_company_name_basic: {e}")
    return None

# --- Main Analyzer Function ---
def analyze_job_text(text: str) -> dict:
    """
    Analyzes job description text to extract key information like skills,
    experience level, and company name.
    Args:
        text: The raw text of the job description.
    Returns:
        A dictionary containing the extracted information.
    """
    if not text or not isinstance(text, str):
        return {
            'skills': ["N/A"], 'experience_years': "N/A",
            'seniority': "N/A", 'company_name': "N/A"
        }

    # Initialize results with defaults
    results = {
        'skills': ["N/A"], 'experience_years': "N/A",
        'seniority': "N/A", 'company_name': "N/A"
    }

    try:
        doc = nlp(text)
        text_lower = text.lower()

        extracted_skills = extract_skills_from_text(text_lower)
        if extracted_skills: results['skills'] = extracted_skills

        years_exp, seniority_lvl = extract_experience_level(text) # Use original text for experience regex
        if years_exp: results['experience_years'] = years_exp
        if seniority_lvl: results['seniority'] = seniority_lvl

        company = extract_company_name_basic(doc)
        if company: results['company_name'] = company

    except Exception as e:
        print(f"An error occurred during job text analysis: {e}")
        # Results will retain defaults if an error occurs

    return results

# --- Test Section ---
if __name__ == '__main__':
    sample_job_description = """
    Senior Software Engineer - Backend (Java/Python)
    ExampleCorp - San Francisco, CA. We are hiring!

    About ExampleCorp
    ExampleCorp is a leading innovator in the tech industry, dedicated to creating solutions that change the world. Our benefits are great.

    We are looking for a Senior Software Engineer with 5+ years of experience in backend development.
    The ideal candidate will have a strong background in Python, Java, and cloud platforms like AWS or GCP.
    Experience with microservices architecture, Docker, and Kubernetes is a big plus. SQL is a must.
    You should be proficient in SQL and NoSQL databases, such as PostgreSQL and MongoDB.
    Responsibilities include designing, developing, and deploying scalable backend services.
    Must have excellent communication skills and problem-solving skills.
    A Bachelor's degree in Computer Science or related field is required. M.S. preferred.
    This is a full-time position. We are also hiring for a Junior Developer role.
    Relevant experience: 3-5 years of professional software development.
    """

    print("--- Analyzing Sample Job Description ---")
    if nlp.meta.get('lang') == 'en' and 'ner' in nlp.pipe_names:
        analysis_results = analyze_job_text(sample_job_description)
        import json
        print(json.dumps(analysis_results, indent=2))
    else:
        print("Skipping test: spaCy model not fully loaded or functional.")

    another_jd = """
    Data Scientist
    DataDriven Inc. is looking for a new team member.
    We need a data scientist with at least 3 years of experience in machine learning and data analysis.
    Skills: Python, R, Pandas, Scikit-learn, TensorFlow.
    SQL knowledge is essential. Join our team! We use Agile.
    """
    print("\n--- Analyzing Another Job Description ---")
    if nlp.meta.get('lang') == 'en' and 'ner' in nlp.pipe_names:
        analysis_results_2 = analyze_job_text(another_jd)
        print(json.dumps(analysis_results_2, indent=2))
    else:
        print("Skipping test: spaCy model not fully loaded or functional.")
    pass
