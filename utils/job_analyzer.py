import spacy
import re
from collections import Counter
from typing import List, Tuple, Optional, Dict, Any # For type hinting

# --- Constants and Pre-compiled Regex ---
# Regex for experience, aiming for specificity.
EXPERIENCE_YEARS_PATTERN = re.compile(
    r"""
    \b                                      # Word boundary
    (?:                                     # Non-capturing group for different formats
        (?:(?:[2-9]|[1-9]\d)\s*(?:to|-|–|—)\s*(?:[2-9]|[1-9]\d)) | # Ranges like "3-5", "10-15"
        (?:(?:[1-9]|[1-9]\d)\s*\+\s*years) |                         # "5+ years"
        (?:(?:[1-9]|[1-9]\d)\+?) |                                  # "5+", "10" (when followed by "years of experience")
        (?:at\s+least\s+\d{1,2}) |                                # "at least 2"
        (?:minimum\s+\d{1,2}) |                                   # "minimum 3"
        (?:(?:a|one|two|three|four|five|six|seven|eight|nine|ten)\s+ # Spelled out numbers "one year", "two to five years"
           (?:to\s+(?:five|six|seven|eight|nine|ten|eleven|twelve))?)
    )
    \s+years?(?:\s+of)?                         # "year" or "years", optionally "of"
    (?:\s*(?:relevant|work|professional)\s+)?  # Optional relevant/work/professional
    experience                                  # The word "experience"
    """,
    re.IGNORECASE | re.VERBOSE # Verbose for readability
)
YEAR_NUMBER_PATTERN = re.compile(r'(\d{1,2})') # Extracts numbers from phrases
ABOUT_COMPANY_PATTERN = re.compile(r"About\s+([A-Z][\w\s.&'-]+)\n", re.IGNORECASE)

# --- spaCy Model Loading ---
try:
    nlp = spacy.load('en_core_web_sm')
    print("Job Analyzer: spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    print("Job Analyzer: spaCy model 'en_core_web_sm' not found. Please ensure it's downloaded (python -m spacy download en_core_web_sm).")
    nlp = spacy.blank("en") # Fallback; NER and other linguistic features will be limited.

# --- Skill Definitions ---
# SKILLS_LIST should be comprehensive and is a good candidate for external configuration (e.g., JSON file).
SKILLS_LIST = sorted(list(set([
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'go', 'rust', 'sql', 'nosql', 'pl/sql', 'perl',
    'html', 'css', 'react', 'angular', 'vue', 'vue.js', 'node.js', 'jquery', 'django', 'flask', 'spring', 'spring boot', '.net', 'asp.net',
    'ruby on rails', 'laravel', 'express.js', 'bootstrap', 'tailwind css', 'sass', 'less', 'graphql', 'restful apis', 'soap apis',
    'mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'cassandra', 'elasticsearch', 'oracle', 'sql server', 'mariadb', 'dynamodb',
    'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes', 'k8s', 'openshift', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'git', 'github', 'gitlab', 'bitbucket', 'svn',
    'linux', 'unix', 'bash scripting', 'powershell', 'serverless', 'aws lambda', 'azure functions',
    'machine learning', 'deep learning', 'nlp', 'natural language processing', 'computer vision', 'data analysis', 'data visualization',
    'data science', 'pandas', 'numpy', 'scipy', 'scikit-learn', 'sklearn', 'tensorflow', 'keras', 'pytorch', 'spark', 'apache spark', 'hadoop',
    'r', 'r programming', 'tableau', 'power bi', 'sas', 'matlab', 'statistics', 'econometrics', 'quantitative analysis',
    'agile', 'scrum', 'kanban', 'waterfall', 'devops principles', 'rest', 'soap', 'apis', 'microservices', 'tdd', 'bdd', 'unit testing',
    'integration testing', 'software architecture', 'solution architecture', 'design patterns', 'system design', 'oop',
    'communication skills', 'teamwork', 'problem-solving skills', 'leadership skills', 'project management', 'product management',
    'analytical skills', 'critical thinking', 'creativity', 'time management skills', 'customer service', 'sales skills', 'marketing strategy',
    'stakeholder management', 'negotiation skills', 'presentation skills', 'technical writing', 'ux/ui design',
    'sap', 'salesforce', 'sharepoint', 'jira', 'confluence', 'slack', 'microsoft office suite', 'excel', 'ms word', 'ms powerpoint', 'autocad', 'photoshop', 'illustrator'
])))


# --- Extraction Functions ---
def extract_skills_from_text(text_lower: str) -> List[str]:
    """
    Extracts skills from lowercased text based on a predefined list.
    Uses regex with word boundaries for more accurate matching.
    """
    found_skills = set()
    for skill in SKILLS_LIST:
        try:
            # \b ensures matching whole words, re.escape handles special characters in skill names
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower): # Search in the already lowercased text
                # Consistent capitalization for display (e.g., "Javascript" -> "JavaScript" if SKILLS_LIST has "javaScript")
                # This requires SKILLS_LIST to have the desired capitalization.
                # For simplicity, using .capitalize() or .upper() for known acronyms.
                if skill.upper() in ['AWS', 'GCP', 'SQL', 'NLP', 'HTML', 'CSS', 'API', 'CI/CD', 'OOP', 'TDD', 'BDD']: # Add other acronyms as needed
                    found_skills.add(skill.upper())
                else:
                    found_skills.add(skill.title() if ' ' in skill else skill.capitalize()) # Title case for multi-word, capitalize for single
        except re.error as e:
            print(f"Regex error for skill '{skill}': {e}") # Log regex issues
            continue
    return sorted(list(found_skills))

def _normalize_experience_phrase(phrase: str) -> str:
    """Normalizes extracted experience phrases (e.g., "at least 2" to "2+ years")."""
    phrase_lower = phrase.lower()
    if 'to' in phrase_lower or '-' in phrase_lower or '–' in phrase_lower or '—' in phrase_lower:
        numbers = YEAR_NUMBER_PATTERN.findall(phrase)
        return f"{numbers[0]}-{numbers[1]} years" if len(numbers) >= 2 else (f"Up to {numbers[0]} years" if numbers else phrase + " years")
    elif '+' in phrase_lower:
        num_match = YEAR_NUMBER_PATTERN.search(phrase)
        return f"{num_match.group(0)}+ years" if num_match else phrase + " years"
    elif 'at least' in phrase_lower or 'minimum' in phrase_lower:
        num_match = YEAR_NUMBER_PATTERN.search(phrase)
        return f"{num_match.group(0)}+ years" if num_match else phrase + " years"
    elif YEAR_NUMBER_PATTERN.search(phrase): # Single number like "5 years experience"
        num_match = YEAR_NUMBER_PATTERN.search(phrase)
        return f"{num_match.group(0)} years" if num_match else phrase + " years"
    # Handle spelled-out numbers (basic cases)
    number_words = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six":"6", "seven":"7", "eight":"8", "nine":"9", "ten":"10"}
    for word, num_str in number_words.items():
        if word in phrase_lower:
            return f"{num_str}+ years" if "+" in phrase_lower or "at least" in phrase_lower or "minimum" in phrase_lower else f"{num_str} years"
    return phrase + " years" # Default if no specific normalization applies

def extract_experience_level(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extracts years of experience and seniority levels from text."""
    years_experience_str: Optional[str] = None
    seniority_str: Optional[str] = None

    match = EXPERIENCE_YEARS_PATTERN.search(text)
    if match:
        years_experience_str = _normalize_experience_phrase(match.group(1).strip())

    seniority_keywords_map = {
        'Senior': [r'\bsenior\b', r'\bsr\.?\b'], 'Lead': [r'\blead\b', r'\bteam lead\b'],
        'Junior': [r'\bjunior\b', r'\bjr\.?\b', r'\bentry-level\b', r'\bgraduate\b'],
        'Mid-Level': [r'\bmid-level\b', r'\bintermediate\b'], 'Principal': [r'\bprincipal\b'],
        'Staff': [r'\bstaff engineer\b', r'\bstaff software\b', r'\bstaff level\b'],
        'Manager': [r'\bmanager\b(?!\s+of\s+product)', r'\bmanaging\b'] # Avoid "Product Manager" if only "Manager" is wanted for seniority
    }
    text_lower = text.lower()
    found_seniorities = set()
    for level, patterns in seniority_keywords_map.items():
        for pattern_str in patterns:
            if re.search(pattern_str, text_lower):
                found_seniorities.add(level)

    # Prioritization for seniority
    priority_order = ['Manager', 'Principal', 'Staff', 'Lead', 'Senior', 'Mid-Level', 'Junior']
    for level in priority_order:
        if level in found_seniorities:
            seniority_str = level
            break

    return years_experience_str, seniority_str

def extract_company_name_basic(doc: spacy.tokens.Doc) -> Optional[str]:
    """Basic company name extraction using NER and heuristics."""
    try:
        about_match = ABOUT_COMPANY_PATTERN.search(doc.text)
        if about_match: return about_match.group(1).strip()

        orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
        if orgs:
            common_noise = {'Inc', 'Ltd', 'LLC', 'Company', 'Corporation', 'Group', 'Solutions', 'Technologies', 'Systems', 'Global'}
            # Filter based on length and noise words, but be less aggressive if it's a known tech skill/company
            filtered_orgs = [
                org for org in orgs
                if (len(org) > 2 and org not in common_noise and org.lower() not in SKILLS_LIST) or \
                   (org.lower() in SKILLS_LIST and len(org.split()) == 1 and org.isupper()) # e.g. AWS, GCP
            ]
            if not filtered_orgs and orgs: # If filtering removed everything, use original orgs if any
                 filtered_orgs = [org for org in orgs if len(org) > 2 and org not in common_noise]


            if filtered_orgs:
                org_counts = Counter(filtered_orgs)
                # Prefer longer, more specific ORG names if counts are similar
                # This needs more sophisticated ranking if multiple ORGs appear
                return org_counts.most_common(1)[0][0]
    except Exception as e:
        print(f"Error in extract_company_name_basic: {e}")
    return None

# --- Main Analyzer Function ---
def analyze_job_text(text: str) -> Dict[str, Any]:
    """
    Analyzes job description text to extract key information.
    Returns a dictionary with extracted data.
    """
    # Default structure for results
    results: Dict[str, Any] = {
        'skills': ["N/A"], 'experience_years': "N/A",
        'seniority': "N/A", 'company_name': "N/A"
    }
    if not text or not isinstance(text, str) or len(text.strip()) < 50: # Basic check for minimal content
        print("Job analysis: Input text is too short or invalid.")
        return results

    try:
        doc = nlp(text)
        text_lower = text.lower() # For case-insensitive operations

        extracted_skills = extract_skills_from_text(text_lower)
        if extracted_skills: results['skills'] = extracted_skills

        years_exp, seniority_lvl = extract_experience_level(text)
        if years_exp: results['experience_years'] = years_exp
        if seniority_lvl: results['seniority'] = seniority_lvl

        company = extract_company_name_basic(doc)
        if company: results['company_name'] = company

    except Exception as e:
        print(f"An error occurred during job text analysis pipeline: {e}")
        # Results will retain defaults if a critical error occurs during processing.
    return results

# --- Test Section ---
if __name__ == '__main__':
    sample_jd_1 = """
    Senior Software Engineer - Backend (Java/Python)
    ExampleCorp - San Francisco, CA. We are hiring! About ExampleCorp: We are great.
    We are looking for a Senior Software Engineer with 5+ years of experience in backend development.
    Skills: Python, Java, AWS, GCP, Docker, Kubernetes, SQL, PostgreSQL, MongoDB, Agile.
    Relevant experience: 3-5 years of professional software development. Must have communication skills.
    """
    sample_jd_2 = "Entry-level Data Analyst. Requires SQL and Python. Minimum two years experience."

    print("--- Analyzing Sample Job Description 1 ---")
    if nlp.meta.get('lang') == 'en' and 'ner' in nlp.pipe_names:
        analysis_1 = analyze_job_text(sample_jd_1)
        import json
        print(json.dumps(analysis_1, indent=2))
    else:
        print("Skipping test: spaCy model not fully loaded or functional.")

    print("\n--- Analyzing Sample Job Description 2 ---")
    if nlp.meta.get('lang') == 'en' and 'ner' in nlp.pipe_names:
        analysis_2 = analyze_job_text(sample_jd_2)
        print(json.dumps(analysis_2, indent=2))
    else:
        print("Skipping test: spaCy model not fully loaded or functional.")
    pass
