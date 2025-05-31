import PyPDF2
import docx
import re
import spacy
from spacy.matcher import Matcher

# --- Constants and Pre-compiled Regex ---
# It's good practice to define constants for regex patterns, especially if complex.
# Compiling regex patterns that are used multiple times can improve performance.
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}") # More comprehensive
SKILL_SECTION_PATTERN = re.compile(
    r"(skills|technical skills|proficiencies|technologies|technical proficiencies)[\s:]*\n((?:[ \t]*(?:[\w\s,+#./()&'-]+)(?:\n|$))+)",
    re.IGNORECASE
)
EDUCATION_SECTION_PATTERN = re.compile(
    r"(education|academic background|qualifications)[\s:]*\n((?:.|\n)+?)(?=\n(?:experience|skills|projects|awards|publications|references|technical skills)|$)",
    re.IGNORECASE
)
EXPERIENCE_SECTION_PATTERN = re.compile(
    r"(experience|work experience|professional experience|employment history)[\s:]*\n((?:.|\n)+?)(?=\n(?:education|skills|projects|awards|publications|references)|$)",
    re.IGNORECASE
)
SUMMARY_SECTION_PATTERN = re.compile(
     r"(summary|objective|profile|about me|professional profile|personal statement)\s*?\n([\s\S]+?)(?=\n\s*(?:experience|skills|education|projects)|$)",
    re.IGNORECASE
)
# For education parsing
DEGREE_PATTERN = re.compile(r'\b(?:B\.?S\.?c?|M\.?S\.?c?|Ph\.?D|M\.?B\.?A|B\.?A\.?|Bachelor(?: of| of Science| of Arts)?|Master(?: of| of Science| of Arts)?|Doctor(?: of Philosophy)?)\b(?: in)?\s*([\w\s,]+)', re.IGNORECASE)
# For dates (general, can be refined for specific contexts like grad date vs. job dates)
DATE_PATTERN_GENERIC = re.compile(r'\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?\d{4}\b|\b\d{4}\s*-\s*\d{4}\b|\bPresent\b', re.IGNORECASE)
JOB_DATE_PATTERN = re.compile(r'\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?\d{4}\s*(?:-|to|–|—)\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?(?:\d{4}|Present|Current)\b', re.IGNORECASE)


# --- spaCy Model Loading ---
try:
    nlp = spacy.load('en_core_web_sm')
    print("spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    print("spaCy model 'en_core_web_sm' not found. Attempting to download...")
    try:
        spacy.cli.download('en_core_web_sm')
        nlp = spacy.load('en_core_web_sm')
        print("spaCy model 'en_core_web_sm' downloaded and loaded successfully.")
    except Exception as e:
        print(f"Could not download or load spaCy model: {e}. NER features will be limited.")
        nlp = spacy.blank("en") # Fallback

# --- Text Extraction ---
def extract_text_from_pdf(file_path: str) -> str | None:
    """
    Extracts text content from a PDF file.
    Args:
        file_path: Path to the PDF file.
    Returns:
        Extracted text as a string, or None if an error occurs.
    """
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
        return text
    except Exception as e:
        print(f"Error extracting text from PDF '{file_path}': {e}")
        return None

def extract_text_from_docx(file_path: str) -> str | None:
    """
    Extracts text content from a DOCX file.
    Args:
        file_path: Path to the DOCX file.
    Returns:
        Extracted text as a string, or None if an error occurs.
    """
    try:
        doc = docx.Document(file_path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX '{file_path}': {e}")
        return None

# --- Core Parsing Functions ---
def parse_name(doc: spacy.tokens.Doc) -> str | None:
    """
    Parses the full name from a spaCy Doc object using NER and pattern matching.
    Args:
        doc: spaCy Doc object of the resume text.
    Returns:
        The extracted full name, or None if not found.
    """
    matcher = Matcher(nlp.vocab)
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]  # Matches two consecutive proper nouns
    matcher.add('NAME', [pattern])
    matches = matcher(doc)
    for _, start, end in matches: # Using _ for match_id as it's not used
        return doc[start:end].text

    for ent in doc.ents: # Fallback to PERSON entity
        if ent.label_ == "PERSON":
            return ent.text
    return None

def parse_email(text: str) -> str | None:
    """
    Parses the email address from text using regex.
    Args:
        text: The text to parse.
    Returns:
        The extracted email address, or None if not found.
    """
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None

def parse_phone(text: str) -> str | None:
    """
    Parses the phone number from text using regex.
    Args:
        text: The text to parse.
    Returns:
        The extracted phone number, or None if not found.
    """
    match = PHONE_PATTERN.search(text)
    return match.group(0) if match else None

def parse_skills(doc: spacy.tokens.Doc, text_lower: str) -> list[str]:
    """
    Parses skills from the resume text using a predefined list and section headers.
    Args:
        doc: spaCy Doc object of the resume text.
        text_lower: Lowercased version of the resume text.
    Returns:
        A sorted list of unique skills found.
    """
    # Consider moving SKILLS_LIST to a separate file or making it more configurable
    skills_list = [
        'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'sql', 'nosql', 'mongodb', 'postgresql',
        'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring boot', 'html', 'css',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'ci/cd',
        'machine learning', 'deep learning', 'nlp', 'natural language processing', 'computer vision',
        'data analysis', 'data science', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
        'agile', 'scrum', 'jira', 'git', 'restful apis', 'microservices',
        'communication', 'teamwork', 'problem solving', 'leadership', 'project management'
        # This list can be significantly expanded
    ]
    found_skills = set()

    # Method 1: Keyword matching in the whole document (already lowercased)
    for skill in skills_list:
        if skill in text_lower: # Direct substring check
            found_skills.add(skill.capitalize())

    # Method 2: Look for specific skill sections
    matches = SKILL_SECTION_PATTERN.finditer(text_lower) # Use pre-compiled regex
    for match in matches:
        section_content = match.group(2).strip()
        section_doc = nlp(section_content) # Process only the section with spaCy
        for token in section_doc:
            if token.lemma_.lower() in skills_list:
                 found_skills.add(token.lemma_.capitalize())
        for skill_phrase in skills_list: # Check for multi-word skills in the section
            if skill_phrase in section_content:
                 found_skills.add(skill_phrase.capitalize())

    return sorted(list(found_skills))

def parse_summary(doc: spacy.tokens.Doc, text: str) -> str | None:
    """
    Parses the summary/objective section from the resume text.
    Args:
        doc: spaCy Doc object of the resume text. (Currently unused, text is sufficient)
        text: The full resume text.
    Returns:
        The extracted summary string, or None if not found.
    """
    match = SUMMARY_SECTION_PATTERN.search(text)
    return match.group(2).strip() if match else None

def _parse_single_education_entry(entry_text: str) -> dict | None:
    """Helper function to parse a single education entry block."""
    if not entry_text.strip() or len(entry_text.strip()) < 10:
        return None

    entry_doc = nlp(entry_text)
    degree_match = DEGREE_PATTERN.search(entry_text)

    degree = None
    if degree_match:
        degree = degree_match.group(1).strip() if degree_match.group(1) else degree_match.group(0).strip()

    institution, date_str = None, None
    for ent in entry_doc.ents:
        if ent.label_ == "ORG" and not institution:
            if any(uni_kw in ent.text.lower() for uni_kw in ['university', 'college', 'institute']):
                institution = ent.text
        elif ent.label_ == "DATE" and not date_str and DATE_PATTERN_GENERIC.search(ent.text):
            date_str = ent.text

    if not date_str: # Fallback regex for dates
        date_match_fallback = DATE_PATTERN_GENERIC.search(entry_text)
        if date_match_fallback: date_str = date_match_fallback.group(0)

    # Basic fallback for institution if not found via NER
    if not institution and degree and degree_match:
        possible_institution_text = entry_text[degree_match.end():]
        if date_str and date_match_fallback: # if date was found by regex
             possible_institution_text = possible_institution_text[:date_match_fallback.start()]
        inst_candidates = re.findall(r'((?:[A-Z][\w\s.&\'()-]+)+)', possible_institution_text) # Slightly more permissive
        if inst_candidates:
            institution = max(inst_candidates, key=len).strip().replace('\n',' ')
            if len(institution.split()) > 7: institution = " ".join(institution.split()[:7]) # Heuristic limit

    if degree or institution or date_str:
        return {
            'degree': degree.strip().rstrip(',') if degree else "N/A",
            'institution': institution.strip().rstrip(',') if institution else "N/A",
            'date': date_str.strip() if date_str else "N/A"
        }
    return None


def parse_education(doc: spacy.tokens.Doc, text: str) -> list[dict]:
    """
    Parses education details from the resume text.
    Args:
        doc: spaCy Doc object of the resume text. (Currently unused, text is sufficient)
        text: The full resume text.
    Returns:
        A list of dictionaries, each representing an education entry.
    """
    education_entries = []
    section_match = EDUCATION_SECTION_PATTERN.search(text)
    if not section_match:
        return education_entries

    education_text = section_match.group(2)
    # Improved splitting logic: consider lines starting with a degree, or major capitalized words (potential institution)
    # This regex attempts to split entries more robustly.
    potential_entries = re.split(r'\n\s*\n+|\n(?=\s*(?:B\.?S|M\.?S|Ph\.?D|Bachelor|Master|Doctor|[A-Z][a-z]+ University|[A-Z][a-z]+ College))', education_text.strip())

    for entry_text in potential_entries:
        try:
            parsed_entry = _parse_single_education_entry(entry_text)
            if parsed_entry:
                education_entries.append(parsed_entry)
        except Exception as e:
            print(f"Error parsing education entry: '{entry_text[:50]}...': {e}")
            continue # Skip problematic entries

    return education_entries

def _parse_single_experience_entry(entry_text: str) -> dict | None:
    """Helper function to parse a single experience entry block."""
    entry_text = entry_text.strip()
    if not entry_text or len(entry_text) < 20:
        return None

    job_title, company, date_range = None, None, None
    description_lines = []

    # Try to find date range first
    date_match = JOB_DATE_PATTERN.search(entry_text)
    entry_text_no_date = entry_text
    if date_match:
        date_range = date_match.group(0)
        entry_text_no_date = entry_text.replace(date_range, "").strip()

    # Heuristic for Title and Company from the first significant line
    lines = entry_text_no_date.split('\n')
    first_line_processed = False
    if lines:
        first_line = lines[0].strip()
        # Common patterns: "Title at Company", "Title, Company", "Title - Company"
        match_title_company = re.match(r'([\w\s.&\'()/-]+?)\s*(?:at|@|,|-)\s*([\w\s.&\'()/-]+)', first_line, re.IGNORECASE)
        if match_title_company:
            job_title = match_title_company.group(1).strip()
            company = match_title_company.group(2).strip()
            first_line_processed = True
        else: # If no clear separator, assume first line is title or title+company
            # NER on the first line to find ORG for company
            first_line_doc = nlp(first_line)
            for ent in first_line_doc.ents:
                if ent.label_ == "ORG" and not company:
                    company = ent.text
            # What remains of the first line (if company found) or whole first line is job_title
            job_title = first_line.replace(company, "").strip() if company else first_line
            first_line_processed = True

    # Fallback NER for company on the whole entry_text_no_date if not found
    if not company:
        entry_doc_no_date = nlp(entry_text_no_date)
        for ent in entry_doc_no_date.ents:
            if ent.label_ == "ORG":
                company = ent.text
                break

    # Description lines
    start_desc_line = 1 if first_line_processed and (job_title or company) else 0
    current_description = []
    for i in range(start_desc_line, len(lines)):
        line_content = lines[i].strip()
        if line_content:
            # Avoid re-capturing company or date if they are on separate lines within description area
            if company and company == line_content: continue
            if date_range and date_range == line_content: continue
            current_description.append(line_content)
    description = "\n".join(current_description).strip()

    if job_title or company or date_range:
        return {
            'job_title': job_title.strip() if job_title else "N/A",
            'company': company.strip() if company else "N/A",
            'date_range': date_range.strip() if date_range else "N/A",
            'description': description if description else "N/A"
        }
    return None


def parse_experience(doc: spacy.tokens.Doc, text: str) -> list[dict]:
    """
    Parses work experience details from the resume text.
    Args:
        doc: spaCy Doc object of the resume text. (Currently unused, text is sufficient)
        text: The full resume text.
    Returns:
        A list of dictionaries, each representing a work experience entry.
    """
    experience_entries = []
    section_match = EXPERIENCE_SECTION_PATTERN.search(text)
    if not section_match:
        return experience_entries

    experience_text = section_match.group(2)
    # Splitting logic for experience entries (improved)
    # Split by two or more newlines, or a newline followed by a potential job title (capitalized words, possibly with 'at' or ',')
    # or a newline followed by a date range.
    job_entry_splits = re.split(
        r'\n\s*\n\s*\n*|\n(?=\s*(?:[A-Z][\w\s.&\'()/-]+(?:Engineer|Developer|Manager|Analyst|Specialist|Lead|Architect|Consultant)\b|[A-Z][\w\s.&\'()/-]+\s*(?:at|@|,|-)\s*[A-Z])|\n\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?\d{4}\s*-\s*)',
        experience_text.strip()
    )

    for entry_text in job_entry_splits:
        try:
            parsed_entry = _parse_single_experience_entry(entry_text)
            if parsed_entry:
                experience_entries.append(parsed_entry)
        except Exception as e:
            print(f"Error parsing experience entry: '{entry_text[:50]}...': {e}")
            continue # Skip problematic entries

    return experience_entries

# --- Main Parsing Orchestrator ---
def parse_resume_text(text: str) -> dict:
    """
    Main function to parse extracted text from a resume to find structured data.
    Uses spaCy for NLP tasks and regex for pattern matching.
    Args:
        text: The raw text content of the resume.
    Returns:
        A dictionary containing parsed resume data.
    """
    if not text or not isinstance(text, str):
        print("Invalid input text for parsing.")
        return {} # Return empty dict for invalid input

    doc = nlp(text)
    text_lower = text.lower()

    # Initialize with default values
    resume_data = {
        "name": "N/A", "email": "N/A", "phone": "N/A",
        "skills": ["N/A"], "summary": "N/A",
        "education": [], "experience": []
    }
    try:
        resume_data["name"] = parse_name(doc) or (text.split('\n')[0].strip() if text.split('\n') and text.split('\n')[0].strip() else "N/A")
        resume_data["email"] = parse_email(text) or "N/A"
        resume_data["phone"] = parse_phone(text) or "N/A"
        resume_data["skills"] = parse_skills(doc, text_lower) or ["N/A"]
        resume_data["summary"] = parse_summary(doc, text) or "N/A" # doc is passed but currently unused by summary

        # Education and Experience can raise errors during their complex parsing
        try:
            resume_data["education"] = parse_education(doc, text)
        except Exception as e:
            print(f"Critical error in parse_education: {e}")
            resume_data["education"] = [] # Ensure it's a list

        try:
            resume_data["experience"] = parse_experience(doc, text)
        except Exception as e:
            print(f"Critical error in parse_experience: {e}")
            resume_data["experience"] = [] # Ensure it's a list

    except Exception as e:
        print(f"An unexpected error occurred during resume parsing: {e}")
        # Ensure basic structure is still returned
        for key, value in resume_data.items():
            if value is None: # Should not happen with defaults, but as a safeguard
                resume_data[key] = "N/A" if not isinstance(value, list) else []

    # Add placeholder dicts if education/experience are empty, for consistent UI handling
    if not resume_data["education"]:
        resume_data["education"] = [{'degree': 'N/A', 'institution': 'N/A', 'date': 'N/A'}]
    if not resume_data["experience"]:
        resume_data["experience"] = [{'job_title': 'N/A', 'company': 'N/A', 'date_range': 'N/A', 'description': 'N/A'}]

    return resume_data

# --- Test Section ---
if __name__ == '__main__':
    sample_text_for_testing = """
Johnathan R. Doe III
123 Main Street, Anytown, USA 12345
(123) 456-7890 | john.doe.test@emaildomain.com | linkedin.com/in/johndoetest | github.com/johndoetest

Summary
Results-driven Senior Software Engineer with 8+ years of experience in developing and leading complex software projects.
Expertise in Python, Java, cloud architectures (AWS, Azure), and DevOps practices. Proven ability to deliver high-quality software solutions.
Seeking a challenging role in a dynamic organization.

Work Experience

Lead Software Developer | QuantumLeap Tech | Jan 2020 – Present
- Spearheaded the development of a new microservices-based platform using Python, Flask, Docker, and Kubernetes on AWS.
- Managed a team of 6 software engineers, providing mentorship and technical guidance.
- Reduced system latency by 25% through performance optimization and architectural improvements.
- Implemented CI/CD pipelines using Jenkins and Ansible, improving deployment frequency by 50%.

Software Engineer | AlphaBeta Solutions | June 2015 - Dec 2019
- Developed and maintained scalable web applications using Java, Spring Boot, and PostgreSQL.
- Collaborated with cross-functional teams to define project requirements and deliver features.
- Contributed to API design and development for third-party integrations.
- Received 'Innovator of the Year' award in 2018 for a novel algorithm design.

Education

Massachusetts Institute of Technology (MIT), Cambridge, MA | Sep 2011 – May 2015
Master of Science (M.S.) in Computer Science
Thesis: Efficient Algorithms for Large-Scale Data Processing

Stanford University, Stanford, CA | Sep 2007 – June 2011
Bachelor of Science (B.S.) in Computer Engineering, Minor in Mathematics
GPA: 3.9/4.0, Magna Cum Laude

Technical Skills
Programming Languages: Python (Expert), Java (Expert), C++, SQL, JavaScript, TypeScript
Frameworks & Libraries: Flask, Django, Spring Boot, React, Angular, Pandas, NumPy, Scikit-learn, TensorFlow
Databases: PostgreSQL, MySQL, MongoDB, Redis
Cloud & DevOps: AWS (EC2, S3, Lambda, EKS), Azure, GCP, Docker, Kubernetes, Jenkins, Ansible, Terraform, Git
Methodologies: Agile, Scrum, DevOps, Microservices, TDD

Projects
AI Resume Analyzer | Python, spaCy, Streamlit
- Developed a tool to parse resumes and match them against job descriptions. (This project!)

Personal Finance Tracker | React, Node.js, MongoDB
- Created a web application for tracking personal expenses and investments.
    """

    print("--- Running Parser in Main (Test Mode) ---")
    if nlp.meta.get('lang') == 'en' and 'ner' in nlp.pipe_names: # More robust check for a functional model
        parsed_data = parse_resume_text(sample_text_for_testing)
        print("\n--- Parsed Data ---")
        import json
        print(json.dumps(parsed_data, indent=2))
    else:
        print("Skipping test run as a functional spaCy model with NER might not be fully loaded.")
    pass
