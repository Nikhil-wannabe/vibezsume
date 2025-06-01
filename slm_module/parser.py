import json
import re
from transformers import pipeline

# --- Constants ---
EXPECTED_FIELDS = {
    "name": None,
    "contact_info": {"email": None, "phone": None, "linkedin": None, "github": None},
    "summary": None,
    "skills": [],
    "education": [], # List of dicts: {'institution': '', 'degree': '', 'dates': '', 'details': ''}
    "experience": [] # List of dicts: {'company': '', 'job_title': '', 'dates': '', 'description': ''}
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}") # Simplified
LINKEDIN_REGEX = re.compile(r"linkedin\.com/in/[a-zA-Z0-9_.-]+")
GITHUB_REGEX = re.compile(r"github\.com/[a-zA-Z0-9_.-]+")

# Section keywords
SECTION_KEYWORDS = {
    "summary": ["summary", "objective", "profile", "about me", "professional profile", "personal statement"],
    "skills": ["skills", "technical skills", "technologies", "proficiencies", "core competencies", "technical proficiencies"],
    "education": ["education", "academic background", "qualifications", "academic training"],
    "experience": ["experience", "work experience", "professional experience", "employment history", "career history"]
}
ALL_SECTION_HEADERS_LIST = []
for key in SECTION_KEYWORDS:
    ALL_SECTION_HEADERS_LIST.extend(SECTION_KEYWORDS[key])
ALL_SECTION_HEADERS_LIST.extend(["contact", "personal details", "projects", "awards", "publications", "references"])
ALL_SECTION_HEADERS_REGEX_PART = "|".join(sorted(list(set(ALL_SECTION_HEADERS_LIST)), key=len, reverse=True))


# --- SLM Loading ---
ner_pipeline = None

def load_slm_model(model_name="dbmdz/bert-large-cased-finetuned-conll03-english"):
    global ner_pipeline
    if ner_pipeline is None:
        try:
            # Using grouped_entities=True is important for NER models like this
            ner_pipeline = pipeline("ner", model=model_name, grouped_entities=True)
            print(f"SLM Model '{model_name}' loaded successfully.")
        except ImportError:
            print("Transformers library not found. pip install transformers torch")
            ner_pipeline = None
        except Exception as e:
            print(f"Error loading SLM model '{model_name}': {e}")
            ner_pipeline = None
    return ner_pipeline

# --- Helper Functions ---
def initialize_parsed_data():
    return json.loads(json.dumps(EXPECTED_FIELDS)) # Deep copy

def get_section_text(full_text, section_keywords):
    # (?i) for case-insensitive matching of keywords
    # (?: ... ) is a non-capturing group
    # DOTALL allows . to match newlines
    # MULTILINE allows ^ and $ to match start/end of lines
    # This regex tries to find a section header and capture text until the next known header or end of doc
    pattern_str = r"(?i)^\s*(" + "|".join(section_keywords) + r")[:\s-]*\n(.*?)(?=\n\s*(?:" + ALL_SECTION_HEADERS_REGEX_PART + r")[:\s-]*\n|$)"
    match = re.search(pattern_str, full_text, re.DOTALL | re.MULTILINE)
    if match:
        return match.group(2).strip()
    return None

def extract_entities_from_text(text, entity_labels):
    if not ner_pipeline or not text:
        return []
    try:
        entities = ner_pipeline(text)
        return [entity['word'] for entity in entities if entity['entity_group'] in entity_labels]
    except Exception as e:
        print(f"Error during NER processing in extract_entities_from_text: {e}")
        return []

# --- Core SLM Parsing Logic ---
def parse_resume_text_with_slm(resume_text: str) -> dict:
    parsed_data = initialize_parsed_data()
    if not resume_text:
        return parsed_data

    pipeline_instance = load_slm_model() # Ensure model is loaded
    if not pipeline_instance:
        print("SLM model not available. Returning default structure with error message.")
        parsed_data["name"] = "ERROR: SLM Model Not Loaded"
        return parsed_data

    # 1. Extract Contact Info using Regex (applied to the whole text)
    parsed_data["contact_info"]["email"] = ", ".join(set(EMAIL_REGEX.findall(resume_text))) or None
    parsed_data["contact_info"]["phone"] = ", ".join(set(PHONE_REGEX.findall(resume_text))) or None
    parsed_data["contact_info"]["linkedin"] = ", ".join(set(LINKEDIN_REGEX.findall(resume_text))) or None
    parsed_data["contact_info"]["github"] = ", ".join(set(GITHUB_REGEX.findall(resume_text))) or None

    # 2. Extract Name using NER (applied to the whole text, take first PER)
    try:
        all_entities = pipeline_instance(resume_text[:500]) # Limit to first 500 chars for name search
        for entity in all_entities:
            if entity['entity_group'] == 'PER':
                parsed_data["name"] = entity['word']
                break
    except Exception as e:
        print(f"Error during NER processing for name: {e}")
        if not parsed_data["name"]: parsed_data["name"] = "Error extracting name"


    # 3. Section-based extraction
    summary_text = get_section_text(resume_text, SECTION_KEYWORDS["summary"])
    if summary_text:
        parsed_data["summary"] = summary_text
    else:
        parsed_data["summary"] = "Not found"

    skills_text = get_section_text(resume_text, SECTION_KEYWORDS["skills"])
    if skills_text:
        extracted_skills = extract_entities_from_text(skills_text, ['MISC', 'ORG'])
        # Supplement with regex for common skills if NER misses them or section is just a list
        common_skills_list = ['python', 'java', 'javascript', 'c\+\+', 'c#', 'sql', 'react', 'angular', 'vue', 'node.js',
                              'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'machine learning', 'data analysis', 'nlp',
                              'spring boot', 'django', 'flask', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'git']
        for skill_keyword in common_skills_list:
            if re.search(r'\b' + skill_keyword + r'\b', skills_text, re.IGNORECASE):
                # Find the actual casing from the text if possible, else capitalize
                match = re.search(r'\b(' + skill_keyword + r')\b', skills_text, re.IGNORECASE)
                extracted_skills.append(match.group(1) if match else skill_keyword.capitalize())
        parsed_data["skills"] = sorted(list(set(extracted_skills))) if extracted_skills else ["Not found in section"]
    else:
        parsed_data["skills"] = ["Skills section not found"]

    education_text = get_section_text(resume_text, SECTION_KEYWORDS["education"])
    if education_text:
        # Naive split by two or more newlines, or by lines starting with common degree prefixes
        edu_entry_texts = re.split(r'\n\s*\n+|\n(?=\s*(?:B\.?S|M\.?S|Ph\.?D|Bachelor|Master|Doctor|Associate|Diploma|Certificate))', education_text)
        for entry_text in edu_entry_texts:
            entry_text_clean = entry_text.strip()
            if not entry_text_clean or len(entry_text_clean) < 10: continue # Skip very short lines

            edu_item = {'institution': "N/A", 'degree': "N/A", 'dates': "N/A", 'details': entry_text_clean}
            entry_entities = extract_entities_from_text(entry_text_clean, ['ORG', 'MISC'])

            institutions = [e['word'] for e in (pipeline_instance(entry_text_clean) or []) if e['entity_group'] == 'ORG' and any(kw in e['word'].lower() for kw in ['university', 'college', 'institute', 'school', 'academy'])]
            degrees_misc = [e['word'] for e in (pipeline_instance(entry_text_clean) or []) if e['entity_group'] == 'MISC'] # MISC might be degree or other details

            if institutions: edu_item['institution'] = ", ".join(institutions)
            # Basic degree name matching from MISC entities
            degree_keywords = ['B.S', 'M.S', 'Ph.D', 'Bachelor', 'Master', 'Doctor', 'Associate', 'Diploma', 'Certificate']
            found_degrees = [d for d in degrees_misc if any(kw.lower() in d.lower() for kw in degree_keywords)]
            if found_degrees: edu_item['degree'] = ", ".join(found_degrees)
            elif degrees_misc: edu_item['degree'] = ", ".join(degrees_misc) # Fallback to all MISC if specific not found

            parsed_data["education"].append(edu_item)
        if not parsed_data["education"]: parsed_data["education"] = [{"details": "No specific entries found in section"}]
    else:
        parsed_data["education"] = [{"details": "Education section not found"}]

    experience_text = get_section_text(resume_text, SECTION_KEYWORDS["experience"])
    if experience_text:
        # Naive split by two or more newlines, or by lines that seem to start a new role (e.g., capitalized words then | or @ or "at")
        exp_entry_texts = re.split(r'\n\s*\n+|\n(?=\s*[A-Z][\w\s,-]+(?:\s*\||\s*@|\s+at\s+)[A-Z][\w\s,-]+|\n\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4})\s*-\s*)', experience_text)
        for entry_text in exp_entry_texts:
            entry_text_clean = entry_text.strip()
            if not entry_text_clean or len(entry_text_clean) < 15: continue

            exp_item = {'company': "N/A", 'job_title': "N/A", 'dates': "N/A", 'description': entry_text_clean}

            # Attempt to get company (ORG) and job title (MISC) from the first few lines of the entry
            first_few_lines = "\n".join(entry_text_clean.split('\n')[:3]) # Process first 3 lines for title/company
            entry_entities = pipeline_instance(first_few_lines) or []

            companies = [e['word'] for e in entry_entities if e['entity_group'] == 'ORG']
            job_titles_misc = [e['word'] for e in entry_entities if e['entity_group'] == 'MISC'] # MISC often catches job titles

            if companies: exp_item['company'] = companies[0] # Take first ORG as company
            if job_titles_misc: exp_item['job_title'] = job_titles_misc[0] # Take first MISC as job title

            # If title not found, try regex for common job title patterns (e.g., "Software Engineer") on first line
            if exp_item['job_title'] == "N/A":
                first_line = entry_text_clean.split('\n')[0]
                job_title_match = re.match(r"^[A-Z][a-zA-Z\s.,'-]+(?:Engineer|Developer|Manager|Analyst|Specialist|Lead|Architect|Consultant|Designer)", first_line)
                if job_title_match:
                    exp_item['job_title'] = job_title_match.group(0).strip()

            parsed_data["experience"].append(exp_item)
        if not parsed_data["experience"]: parsed_data["experience"] = [{"description": "No specific entries found in section"}]
    else:
        parsed_data["experience"] = [{"description": "Experience section not found"}]

    return parsed_data

# --- Main function for testing ---
if __name__ == '__main__':
    load_slm_model()

    if ner_pipeline is None:
        print("SLM Model could not be loaded. Aborting test.")
    else:
        sample_resume_text = """
        Dr. Jane Emily Doe
        San Francisco, CA | (555) 123-4567 | jane.doe@personalemail.com
        linkedin.com/in/janedoeexample | github.com/janedoehub

        Summary
        A highly accomplished Data Scientist and AI Researcher with over 12 years of experience in machine learning,
        natural language processing, and predictive analytics. Passionate about leveraging data to solve complex problems
        and drive innovation. Proven ability to lead research projects and develop cutting-edge AI solutions.

        Technical Skills
        - Programming: Python (Expert), R (Proficient), SQL, Scala, Java
        - ML/DL Frameworks: TensorFlow, PyTorch, Keras, Scikit-learn, Hugging Face Transformers
        - NLP: NLTK, SpaCy, Gensim, BERT, GPT models
        - Big Data: Apache Spark, Hadoop, Kafka, Hive
        - Cloud Platforms: AWS (Sagemaker, EC2, S3), Azure ML, GCP AI Platform
        - Databases: PostgreSQL, MySQL, MongoDB, Elasticsearch
        - Tools: Git, Docker, Kubernetes, Jupyter Notebooks, Airflow

        Professional Experience

        Lead AI Researcher | FutureTech Innovations Ltd. | Seattle, WA | Jan 2019 - Present
        - Spearheaded a team of 8 researchers and engineers on projects related to NLP and computer vision.
        - Developed and deployed a novel sentiment analysis model that improved accuracy by 15%.
        - Published 5+ papers in top-tier AI conferences (e.g., NeurIPS, ICML).
        - Secured $2M in research grants.

        Senior Data Scientist | DataDriven Corp. | New York, NY | June 2015 - Dec 2018
        - Designed and implemented machine learning models for customer churn prediction and fraud detection.
        - Utilized Python, R, and Spark to analyze large datasets and extract actionable insights.
        - Collaborated with engineering and product teams to integrate ML solutions into products.

        Education

        Ph.D. in Computer Science (Specialization: AI) | Stanford University, Stanford, CA | 2011 - 2015
        - Dissertation: "Novel Architectures for Deep Neural Networks in NLP"
        - Advisor: Prof. John Smith

        Master of Science in Data Science | Columbia University, New York, NY | 2009 - 2011

        Bachelor of Engineering in Computer Engineering | MIT, Cambridge, MA | 2005 - 2009
        - Graduated Summa Cum Laude
        """

        print("--- Running SLM Resume Parser (Implemented) ---")
        extracted_data = parse_resume_text_with_slm(sample_resume_text)
        print("\n--- Parsed Data ---")
        print(json.dumps(extracted_data, indent=2))
        print("\n--- SLM Parser Test Complete ---")
