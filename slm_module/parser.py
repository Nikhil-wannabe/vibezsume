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
PHONE_REGEX = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}") # Simplified phone regex
LINKEDIN_REGEX = re.compile(r"linkedin\.com/in/[a-zA-Z0-9_.-]+")
GITHUB_REGEX = re.compile(r"github\.com/[a-zA-Z0-9_.-]+")

# Date Regex Patterns for Education and Experience
# Order matters: more specific patterns should come before general ones.
DATE_REGEX_PATTERNS = [
    # Jan 2020 - Dec 2022, Jan. 2020 - Dec. 2022
    re.compile(r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s\d{4}\s*-\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s\d{4})\b", re.IGNORECASE),
    # Jan 2020 - Present, Jan. 2020 - Current
    re.compile(r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s\d{4}\s*-\s*(?:Present|Current))\b", re.IGNORECASE),
    # 2020 - 2022
    re.compile(r"\b(\d{4}\s*-\s*\d{4})\b"),
    # 2020 - Present / Current
    re.compile(r"\b(\d{4}\s*-\s*(?:Present|Current))\b", re.IGNORECASE),
    # Graduated Month Year, Graduated Year
    re.compile(r"\b(Graduated\s(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s)?\d{4})\b", re.IGNORECASE),
    # Month Year (e.g., for a single date like graduation or start/end of a short course)
    re.compile(r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s\d{4})\b", re.IGNORECASE),
    # Season Year (e.g. Fall 2020, Spring 2021)
    re.compile(r"\b((?:Spring|Summer|Fall|Winter)\s\d{4})\b", re.IGNORECASE),
    # Year (as a fallback, could be start or end year if other patterns fail)
    re.compile(r"\b(\d{4})\b")
]

# Section keywords
SECTION_KEYWORDS = {
    "summary": ["summary", "objective", "profile", "about me", "professional profile", "personal statement"],
    "skills": ["skills", "technical skills", "technologies", "proficiencies", "core competencies", "technical proficiencies"],
    "education": ["education", "academic background", "qualifications", "academic training"],
    "experience": ["experience", "work experience", "professional experience", "employment history", "career history"]
}
ALL_SECTION_HEADERS_LIST = [] # Dynamically build a list of all known section headers for regex splitting
for key in SECTION_KEYWORDS:
    ALL_SECTION_HEADERS_LIST.extend(SECTION_KEYWORDS[key])
# Add other common headers not explicitly managed by SECTION_KEYWORDS for more robust section splitting
ALL_SECTION_HEADERS_LIST.extend(["contact", "personal details", "contact information", "projects", "awards", "publications", "references", "achievements", "certifications", "languages"])
# Sort by length (desc) to match longer phrases first (e.g., "professional experience" before "experience")
ALL_SECTION_HEADERS_REGEX_PART = "|".join(sorted(list(set(ALL_SECTION_HEADERS_LIST)), key=len, reverse=True))


# --- SLM Loading ---
ner_pipeline = None

def load_slm_model(model_name="dbmdz/bert-large-cased-finetuned-conll03-english"):
    """
    Loads the Named Entity Recognition (NER) pipeline model from Hugging Face Transformers.

    This function initializes the `ner_pipeline` global variable if it's not already loaded.
    It uses a specified model or a default one. `grouped_entities=True` is used to
    combine token parts of a single entity (e.g., "New" and "York" into "New York").

    Args:
        model_name (str): The name of the NER model to load from Hugging Face Model Hub.

    Returns:
        transformers.pipelines.Pipeline or None: The loaded NER pipeline if successful,
                                                 otherwise None.
    """
    global ner_pipeline
    if ner_pipeline is None:
        try:
            # Using grouped_entities=True is important for NER models like this
            ner_pipeline = pipeline("ner", model=model_name, grouped_entities=True)
            print(f"SLM Model '{model_name}' loaded successfully.")
        except ImportError:
            print("Transformers library not found. Please install it: pip install transformers torch")
            ner_pipeline = None
        except Exception as e:
            print(f"Error loading SLM model '{model_name}': {e}")
            ner_pipeline = None
    return ner_pipeline

# --- Helper Functions ---
def initialize_parsed_data() -> dict:
    """
    Creates and returns a deep copy of the EXPECTED_FIELDS dictionary.

    This ensures that each parsing session starts with a fresh, empty structure
    without modifying the global constant.

    Returns:
        dict: A new dictionary structured according to EXPECTED_FIELDS.
    """
    return json.loads(json.dumps(EXPECTED_FIELDS)) # Deep copy for a fresh structure

def get_section_text(full_text: str, section_keywords: list) -> str | None:
    """
    Extracts the text content of a specific section from the full resume text.

    It uses regex to find a section header (from `section_keywords`) and captures
    all text following it until the next known section header (from `ALL_SECTION_HEADERS_REGEX_PART`)
    or the end of the document.

    Args:
        full_text (str): The entire resume text.
        section_keywords (list): A list of keywords that identify the start of the
                                 desired section (e.g., ["experience", "work experience"]).

    Returns:
        str or None: The extracted text of the section if found, otherwise None.
    """
    # (?i) for case-insensitive matching of section keywords.
    # (?: ... ) is a non-capturing group.
    # DOTALL allows '.' to match newlines, crucial for multi-line section content.
    # MULTILINE allows '^' and '$' to match start/end of lines for header detection.
    # This regex tries to find a section header and capture text until the next known header or end of doc.
    # It looks for a line starting with one of the section_keywords, followed by a colon or whitespace,
    # then captures everything until a line that looks like another section header or end of text.
    pattern_str = r"(?i)^\s*(" + "|".join(section_keywords) + r")[:\s-]*\n(.*?)(?=\n\s*(?:" + ALL_SECTION_HEADERS_REGEX_PART + r")[:\s-]*\n|\Z)"
    match = re.search(pattern_str, full_text, re.DOTALL | re.MULTILINE)
    if match:
        return match.group(2).strip() # Group 2 contains the section content
    return None

def extract_entities_from_text(text: str, entity_labels: list) -> list:
    """
    Extracts entities of specified types from a given text using the loaded NER model.

    Args:
        text (str): The text to process.
        entity_labels (list): A list of entity labels to extract (e.g., ['PER', 'ORG', 'LOC']).

    Returns:
        list: A list of extracted entity words (strings). Returns an empty list if
              the NER pipeline is not available, text is empty, or an error occurs.
    """
    if not ner_pipeline or not text:
        return []
    try:
        entities = ner_pipeline(text)
        # Filters entities based on the provided labels and returns their 'word' attribute.
        return [entity['word'] for entity in entities if entity['entity_group'] in entity_labels]
    except Exception as e:
        print(f"Error during NER processing in extract_entities_from_text: {e}")
        return []

def extract_dates(text: str, patterns: list) -> str | None:
    """
    Extracts date-like strings from text using a list of regex patterns.

    Args:
        text (str): The text to search for dates.
        patterns (list): A list of compiled regex objects for date matching.

    Returns:
        str or None: The first matched date string, or a concatenation if multiple
                     distinct useful dates are found (e.g. start and end from different patterns).
                     Returns None if no pattern matches.
    """
    if not text:
        return None
    
    found_dates = []
    for pattern in patterns:
        matches = pattern.findall(text)
        for match in matches:
            # If the pattern captures a group, match is a tuple or string.
            # We take the first element if it's a tuple (assuming group(1) is the desired date).
            date_str = match[0] if isinstance(match, tuple) else match
            if date_str and date_str.strip():
                found_dates.append(date_str.strip())
    
    if not found_dates:
        return None
    
    # Simple strategy: join unique found dates. More sophisticated logic could be added
    # here to select the "best" or "most complete" date range if multiple are found.
    # For now, we ensure uniqueness and join.
    unique_dates = sorted(list(set(found_dates)), key=text.find) # Sort by appearance order
    
    # Attempt to consolidate if we have multiple partial dates like "Month Year" and "Year"
    # This is a basic consolidation, can be made more robust.
    if len(unique_dates) > 1:
        # If one date is a year and another is Month Year, prefer Month Year or combine.
        # Example: "2020" and "Jan 2020 - Dec 2022". The longer one is usually better.
        # Prioritize longer, more complete date ranges.
        unique_dates.sort(key=len, reverse=True)
        # Return the most comprehensive one, or a combination if they seem to form a range.
        # For now, just return the longest one found. If multiple are equally long and different,
        # joining them might be an option, but it can also create confusing date strings.
        # Let's return the first (longest) match for now.
        return unique_dates[0] 
        # Alternative: return " | ".join(unique_dates) if more than one, but might be noisy.

    return unique_dates[0] if unique_dates else None

# --- Core SLM Parsing Logic ---
def parse_resume_text_with_slm(resume_text: str) -> dict:
    """
    Parses the entire resume text to extract structured information.

    It uses a combination of regex for contact information and section splitting,
    and an SLM (NER model) for entity recognition (like name, organizations, locations).

    Args:
        resume_text (str): The full text of the resume.

    Returns:
        dict: A dictionary containing the parsed information, structured according
              to EXPECTED_FIELDS.
    """
    parsed_data = initialize_parsed_data()
    if not resume_text:
        return parsed_data

    pipeline_instance = load_slm_model() # Ensure model is loaded
    if not pipeline_instance:
        print("SLM model not available. Returning default structure with error message.")
        parsed_data["name"] = "ERROR: SLM Model Not Loaded" # Indicate error in parsed output
        return parsed_data

    # 1. Extract Contact Info using Regex (applied to the whole text for robustness)
    parsed_data["contact_info"]["email"] = ", ".join(set(EMAIL_REGEX.findall(resume_text))) or None
    parsed_data["contact_info"]["phone"] = ", ".join(set(PHONE_REGEX.findall(resume_text))) or None
    parsed_data["contact_info"]["linkedin"] = ", ".join(set(LINKEDIN_REGEX.findall(resume_text))) or None
    parsed_data["contact_info"]["github"] = ", ".join(set(GITHUB_REGEX.findall(resume_text))) or None

    # 2. Extract Name using NER (applied to the beginning of the text, take first PER entity)
    try:
        # Using the first ~500 characters, as names usually appear at the top.
        name_entities = pipeline_instance(resume_text[:500])
        for entity in name_entities:
            if entity['entity_group'] == 'PER': # 'PER' is commonly used for Person names
                parsed_data["name"] = entity['word']
                break # Take the first person entity found
    except Exception as e:
        print(f"Error during NER processing for name: {e}")
        if not parsed_data["name"]: parsed_data["name"] = "Error extracting name"


    # 3. Section-based extraction
    # Summary Section
    summary_text = get_section_text(resume_text, SECTION_KEYWORDS["summary"])
    if summary_text:
        parsed_data["summary"] = summary_text
    else:
        parsed_data["summary"] = "Summary section not found or not clearly demarcated."

    # Skills Section
    skills_text = get_section_text(resume_text, SECTION_KEYWORDS["skills"])
    if skills_text:
        # NER can find skills tagged as MISC or sometimes ORG (e.g. "Amazon Web Services")
        extracted_skills = extract_entities_from_text(skills_text, ['MISC', 'ORG'])
        # Supplement with regex for common skills if NER misses them or section is just a list.
        # This is a simple keyword search; more advanced skill extraction could be used.
        common_skills_list = [
            'python', 'java', 'javascript', 'c\+\+', 'c#', 'sql', 'react', 'angular', 'vue', 'node.js', 'ruby', 'php',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
            'machine learning', 'data analysis', 'nlp', 'computer vision', 'deep learning',
            'spring boot', 'django', 'flask', 'express.js', '.net',
            'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
            'git', 'jira', 'confluence', 'agile', 'scrum', 'devops', 'ci/cd',
            'html', 'css', 'restful apis', 'graphql', 'microservices',
            'data visualization', 'bi tools', 'tableau', 'power bi',
            'project management', 'product management'
        ]
        # Regex to find whole words, case-insensitive
        for skill_keyword_pattern in common_skills_list:
            # Escape '+' for regex if it's part of a skill name like 'C++'
            safe_skill_keyword = skill_keyword_pattern.replace('+', '\+')
            # Search for the skill in the skills_text
            if re.search(r'\b' + safe_skill_keyword + r'\b', skills_text, re.IGNORECASE):
                # Try to find the original casing from the text
                match = re.search(r'\b(' + safe_skill_keyword + r')\b', skills_text, re.IGNORECASE)
                skill_to_add = match.group(1) if match else skill_keyword_pattern
                if skill_to_add not in extracted_skills: # Avoid duplicates if NER already found it
                    extracted_skills.append(skill_to_add)
        
        parsed_data["skills"] = sorted(list(set(extracted_skills))) if extracted_skills else ["Skills not specifically itemized or section not found."]
    else:
        parsed_data["skills"] = ["Skills section not found."]

    # Education Section
    education_text_full = get_section_text(resume_text, SECTION_KEYWORDS["education"])
    if education_text_full:
        # Split education section into entries. Common delimiters are multiple newlines,
        # or lines starting with degree types (B.S., M.S., Ph.D., etc.).
        edu_entry_texts = re.split(
            r'\n\s*\n+|\n(?=\s*(?:B\.?S|M\.?S|Ph\.?D|Bachelor|Master|Doctor|Associate|Diploma|Certificate|B\.A|M\.A|MBA|B\.Eng|M\.Eng)\b)',
            education_text_full, flags=re.IGNORECASE
        )
        for entry_text in edu_entry_texts:
            entry_text_clean = entry_text.strip()
            if not entry_text_clean or len(entry_text_clean) < 10: # Skip very short or empty lines
                continue

            edu_item = {'institution': "N/A", 'degree': "N/A", 'dates': "N/A", 'details': ""}
            
            # Extract dates first
            extracted_date = extract_dates(entry_text_clean, DATE_REGEX_PATTERNS)
            if extracted_date:
                edu_item['dates'] = extracted_date
                # Remove date string from entry_text_clean to avoid re-parsing or including in details
                entry_text_clean = entry_text_clean.replace(extracted_date, "").strip()

            # Use NER to find institutions (ORG) and potentially degrees (MISC)
            # Limiting to ORG for institution and MISC for degree is a heuristic.
            entry_entities = pipeline_instance(entry_text_clean) or []
            
            institutions = [e['word'] for e in entry_entities if e['entity_group'] == 'ORG' and any(kw in e['word'].lower() for kw in ['university', 'college', 'institute', 'school', 'academy', 'polytechnic'])]
            if institutions:
                edu_item['institution'] = ", ".join(institutions)
                for inst in institutions: # Remove found institution from text
                    entry_text_clean = entry_text_clean.replace(inst, "").strip()
            
            # Degree extraction: Combine NER (MISC) and keyword matching for robustness
            degree_keywords = ['B\.S', 'M\.S', 'Ph\.D', 'Bachelor', 'Master', 'Doctor', 'Associate', 'Diploma', 'Certificate', 'B\.A', 'M\.A', 'MBA', 'B\.Eng', 'M\.Eng', 'BSc', 'MSc']
            degrees_misc_ner = [e['word'] for e in entry_entities if e['entity_group'] == 'MISC'] # MISC might catch degree or other details
            
            found_degrees_list = []
            # Check NER MISC entities first
            for misc_entity in degrees_misc_ner:
                for keyword in degree_keywords: # Check if MISC entity looks like a degree
                    if re.search(r'\b' + keyword.replace('.',r'\.?') + r'\b', misc_entity, re.IGNORECASE):
                        if misc_entity not in found_degrees_list:
                             found_degrees_list.append(misc_entity)
            
            # Regex search for degrees in the remaining text if NER didn't pick them up clearly
            if not found_degrees_list:
                for keyword in degree_keywords:
                    match = re.search(r'\b(' + keyword.replace('.',r'\.?') + r'[\w\s]*)', entry_text_clean, re.IGNORECASE)
                    if match:
                        # Try to get a more complete degree name, e.g., "Bachelor of Science in CS"
                        full_degree_match = re.search(r'\b(' + keyword.replace('.',r'\.?') + r'(?:\s+(?:of|in)\s+[\w\s]+)?)', entry_text_clean, re.IGNORECASE)
                        deg_text = (full_degree_match.group(1) if full_degree_match else match.group(1)).strip().rstrip(',')
                        if deg_text not in found_degrees_list:
                            found_degrees_list.append(deg_text)

            if found_degrees_list:
                edu_item['degree'] = ", ".join(sorted(list(set(found_degrees_list)), key=len, reverse=True)) # Longest first
                for deg in found_degrees_list: # Remove found degree from text
                    # Need careful replace, especially if degree is a substring of something else
                    entry_text_clean = re.sub(r'\b' + re.escape(deg) + r'\b', "", entry_text_clean, flags=re.IGNORECASE).strip()
            
            # What's left is details
            edu_item['details'] = re.sub(r'\s{2,}', ' ', entry_text_clean).strip() # Clean up multiple spaces

            parsed_data["education"].append(edu_item)
            
        if not parsed_data["education"]: # If loop didn't add any items
            parsed_data["education"] = [{"details": "No specific education entries parsed from section.", 'institution': 'N/A', 'degree': 'N/A', 'dates': 'N/A'}]
    else:
        parsed_data["education"] = [{"details": "Education section not found.", 'institution': 'N/A', 'degree': 'N/A', 'dates': 'N/A'}]

    # Experience Section
    experience_text_full = get_section_text(resume_text, SECTION_KEYWORDS["experience"])
    if experience_text_full:
        # Split experience section by common delimiters: multiple newlines, or lines indicating a new role
        # This regex looks for newlines followed by typical start of an experience entry (e.g., date range, or Title | Company)
        exp_entry_texts = re.split(
            r'\n\s*\n+|\n(?=\s*(?:[A-Z][\w\s,-]+(?:engineer|developer|manager|analyst|specialist|lead|architect|consultant|designer|intern|associate)\b.*?\s*(?:\||@|at)\s+[A-Z])|\n\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present|Current|\d{4})\b.*?-))',
            experience_text_full, flags=re.IGNORECASE | re.MULTILINE
        )
        for entry_text in exp_entry_texts:
            entry_text_clean = entry_text.strip()
            if not entry_text_clean or len(entry_text_clean) < 15: # Skip short/empty lines
                continue

            exp_item = {'company': "N/A", 'job_title': "N/A", 'dates': "N/A", 'description': ""}
            
            # Extract dates first
            extracted_date = extract_dates(entry_text_clean, DATE_REGEX_PATTERNS)
            if extracted_date:
                exp_item['dates'] = extracted_date
                # Remove date string from entry_text_clean to avoid re-parsing
                # Use regex to remove the date more robustly, avoiding partial word removal
                # Ensure the date is removed as a whole word/phrase
                entry_text_clean = re.sub(r'\b' + re.escape(extracted_date) + r'\b', '', entry_text_clean, count=1, flags=re.IGNORECASE).strip()
                entry_text_clean = entry_text_clean.replace(extracted_date, "").strip() # Fallback, less precise

            # Use NER on the first few lines for company (ORG) and job title (MISC)
            # Common pattern: Title at Company, or Title | Company, or Company - Title
            first_few_lines = "\n".join(entry_text_clean.split('\n')[:3]) # Analyze first 3 lines for these key entities
            entry_entities = pipeline_instance(first_few_lines) or []

            companies_ner = [e['word'] for e in entry_entities if e['entity_group'] == 'ORG']
            job_titles_ner_misc = [e['word'] for e in entry_entities if e['entity_group'] == 'MISC'] # MISC often catches job titles

            # Assign Company
            if companies_ner:
                exp_item['company'] = companies_ner[0] # Assume first ORG is company
                entry_text_clean = entry_text_clean.replace(companies_ner[0], "").strip() # Remove from text

            # Assign Job Title: Prioritize NER MISC, then regex for common titles if NER fails
            if job_titles_ner_misc:
                exp_item['job_title'] = job_titles_ner_misc[0]
                entry_text_clean = entry_text_clean.replace(job_titles_ner_misc[0], "").strip()
            else: # Fallback to regex on the first line if NER MISC was not helpful for title
                first_line = entry_text_clean.split('\n')[0].strip()
                # Regex for job titles: sequence of capitalized words, common role keywords
                job_title_match = re.match(r"^([A-Z][a-zA-Z\s.,'-]*(?:Engineer|Developer|Manager|Analyst|Specialist|Lead|Architect|Consultant|Designer|Intern|Scientist|Coordinator|Representative|Associate|President|Director|VP|Vice President)\b)", first_line, re.IGNORECASE)
                if job_title_match:
                    title_text = job_title_match.group(0).strip().rstrip(',')
                    exp_item['job_title'] = title_text
                    entry_text_clean = entry_text_clean.replace(title_text, "", 1).strip() # Remove only the first occurrence

            # The remaining text is considered the description (responsibilities, achievements)
            # Clean up: remove leading/trailing hyphens, bullets, newlines, multiple spaces
            description_cleaned = re.sub(r'^\s*[-*]\s*', '', entry_text_clean, flags=re.MULTILINE) # Remove leading bullets/hyphens
            description_cleaned = re.sub(r'\s{2,}', ' ', description_cleaned).strip() # Normalize spaces
            exp_item['description'] = description_cleaned

            parsed_data["experience"].append(exp_item)
            
        if not parsed_data["experience"]: # If loop didn't add any
             parsed_data["experience"] = [{"description": "No specific experience entries parsed.", 'company': 'N/A', 'job_title': 'N/A', 'dates': 'N/A'}]
    else:
        parsed_data["experience"] = [{"description": "Experience section not found.", 'company': 'N/A', 'job_title': 'N/A', 'dates': 'N/A'}]

    return parsed_data

# --- Main function for testing ---
if __name__ == '__main__':
    # This ensures the model is loaded when the script is run directly for testing.
    load_slm_model()

    if ner_pipeline is None:
        print("SLM Model could not be loaded. Aborting test run in __main__.")
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
        - Programming: Python (Expert), R (Proficient), SQL, Scala, Java, C++
        - ML/DL Frameworks: TensorFlow, PyTorch, Keras, Scikit-learn, Hugging Face Transformers
        - NLP: NLTK, SpaCy, Gensim, BERT, GPT models
        - Big Data: Apache Spark, Hadoop, Kafka, Hive
        - Cloud Platforms: AWS (Sagemaker, EC2, S3), Azure ML, GCP AI Platform
        - Databases: PostgreSQL, MySQL, MongoDB, Elasticsearch
        - Tools: Git, Docker, Kubernetes, Jupyter Notebooks, Airflow, Jira

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
        - Mentored junior data scientists.

        Data Scientist Intern | BigData Co. | Remote | May 2014 - Aug 2014
        - Assisted senior data scientists with data cleaning and exploratory data analysis.
        - Contributed to the development of a recommendation system.

        Education

        Ph.D. in Computer Science (Specialization: AI) | Stanford University, Stanford, CA | 2011 - 2015
        - Dissertation: "Novel Architectures for Deep Neural Networks in NLP"
        - Advisor: Prof. John Smith
        - Relevant Coursework: Advanced Machine Learning, Deep Learning, Statistical NLP

        Master of Science in Data Science | Columbia University, New York, NY | 2009 - 2011
        - Thesis: "Scalable Algorithms for Topic Modeling"

        Bachelor of Engineering in Computer Engineering | MIT, Cambridge, MA | Graduated May 2009
        - Graduated Summa Cum Laude
        - Senior Project: "Embedded System for Real-time Object Detection"
        """

        print("--- Running SLM Resume Parser (with enhancements) ---")
        extracted_data = parse_resume_text_with_slm(sample_resume_text)
        
        print("\n--- Parsed Data (Enhanced) ---")
        print(json.dumps(extracted_data, indent=2))
        
        # Example: Verify if dates were extracted for experience
        if extracted_data.get("experience"):
            for exp in extracted_data["experience"]:
                if "dates" in exp and exp["dates"] != "N/A":
                    print(f"Found dates for experience at {exp.get('company', 'N/A')}: {exp['dates']}")
                if "description" in exp and exp["description"]:
                    print(f"Found description for {exp.get('job_title', 'N/A')}: First 50 chars: '{exp['description'][:50]}...'")


        if extracted_data.get("education"):
            for edu in extracted_data["education"]:
                if "dates" in edu and edu["dates"] != "N/A":
                    print(f"Found dates for education at {edu.get('institution', 'N/A')}: {edu['dates']}")
                if "details" in edu and edu["details"]:
                     print(f"Found details for {edu.get('degree', 'N/A')}: First 50 chars: '{edu['details'][:50]}...'")

        print("\n--- SLM Parser Test Complete (Enhanced) ---")
