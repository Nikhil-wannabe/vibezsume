import PyPDF2
import docx
import re
import spacy
from spacy.matcher import Matcher
from typing import List, Dict, Optional, Any # For type hinting

# --- Constants and Pre-compiled Regex ---
# Using re.IGNORECASE for most patterns to simplify variations in section headers etc.
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}")
# SKILL_SECTION_PATTERN: Used within parse_skills, kept local there for now if SKILLS_LIST changes.
EDUCATION_SECTION_PATTERN = re.compile(
    r"\n\s*(Education|Academic Background|Qualifications)\s*[:\n]", re.IGNORECASE
)
EXPERIENCE_SECTION_PATTERN = re.compile(
    r"\n\s*(Experience|Work Experience|Professional Experience|Employment History)\s*[:\n]", re.IGNORECASE
)
SUMMARY_SECTION_PATTERN = re.compile(
     r"\n\s*(Summary|Objective|Profile|About Me|Professional Profile|Personal Statement)\s*[:\n]", re.IGNORECASE
)
# DEGREE_PATTERN: Used in _parse_single_education_entry
# DATE_PATTERN_GENERIC: Used in _parse_single_education_entry
# JOB_DATE_PATTERN: Used in _parse_single_experience_entry

# Section Enders: Keywords that often signify the end of a major section.
# This helps in segmenting the resume text.
SECTION_ENDERS_PATTERN = re.compile(
    r"\n\s*(?:Education|Experience|Skills|Projects|Awards|Publications|References|Technical Skills|Work Experience|Professional Experience|Employment History|Academic Background|Qualifications|Interests|Languages|Certifications)\s*[:\n]",
    re.IGNORECASE
)


# --- spaCy Model Loading ---
try:
    nlp = spacy.load('en_core_web_sm')
    print("Resume Parser: spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    print("Resume Parser: spaCy model 'en_core_web_sm' not found. Attempting to download...")
    try:
        spacy.cli.download('en_core_web_sm')
        nlp = spacy.load('en_core_web_sm')
        print("Resume Parser: spaCy model 'en_core_web_sm' downloaded and loaded successfully.")
    except Exception as e:
        print(f"Resume Parser: Could not download or load spaCy model: {e}. NER features will be limited.")
        nlp = spacy.blank("en")

# --- Text Extraction ---
def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Extracts text content from a PDF file."""
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
        return text if text.strip() else None # Return None if only whitespace
    except Exception as e:
        print(f"Error extracting text from PDF '{file_path}': {e}")
        return None

def extract_text_from_docx(file_path: str) -> Optional[str]:
    """Extracts text content from a DOCX file."""
    try:
        doc_obj = docx.Document(file_path)
        text = "\n".join(paragraph.text for paragraph in doc_obj.paragraphs)
        return text if text.strip() else None # Return None if only whitespace
    except Exception as e:
        print(f"Error extracting text from DOCX '{file_path}': {e}")
        return None

# --- Core Parsing Functions ---
def parse_name(doc: spacy.tokens.Doc, text_lines: List[str]) -> Optional[str]:
    """Parses the full name. Prefers NER, then pattern matching, then first sensible line."""
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()

    matcher = Matcher(nlp.vocab) # Moved Matcher instantiation inside for safety if nlp is blank
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    matcher.add('FULL_NAME_PROPN', [pattern])
    matches = matcher(doc[:300]) # Search near the beginning
    for _, start, end in matches:
        name_candidate = doc[start:end].text.strip()
        if len(name_candidate.split()) <= 3: # Avoid overly long "names"
             return name_candidate

    # Fallback: First non-empty line that seems like a name (heuristic)
    if text_lines:
        first_line = text_lines[0].strip()
        if len(first_line.split()) <= 4 and re.match(r"^[A-Z][a-zA-Z\s.-]*$", first_line): # Starts with Cap, few words
            return first_line
    return None

def parse_email(text: str) -> Optional[str]:
    """Parses the email address from text using regex."""
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None

def parse_phone(text: str) -> Optional[str]:
    """Parses the phone number from text using regex."""
    match = PHONE_PATTERN.search(text)
    return match.group(0) if match else None

def parse_skills(doc: spacy.tokens.Doc, text_lower: str) -> List[str]:
    """Parses skills using a predefined list, NER (for ORG/PRODUCT), and section headers."""
    # SKILLS_LIST can be externalized to a JSON or text file for easier management.
    skills_list_keywords = [
        'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'sql', 'nosql', 'mongodb', 'postgresql',
        'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring boot', 'html', 'css', 'scss', 'sass',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'ci/cd', 'jenkins',
        'machine learning', 'deep learning', 'nlp', 'natural language processing', 'computer vision', 'ai',
        'data analysis', 'data science', 'data visualization', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
        'agile', 'scrum', 'jira', 'git', 'github', 'gitlab', 'restful apis', 'microservices', 'api design',
        'communication', 'teamwork', 'problem solving', 'leadership', 'project management', 'product management',
        'big data', 'spark', 'hadoop', 'kafka', 'data warehousing', 'etl', 'data modeling', 'statistics',
        'cybersecurity', 'penetration testing', 'cryptography', 'network security', 'siem', 'ui/ux design'
    ]
    found_skills = set()

    # Method 1: Keyword matching (whole document)
    for skill in skills_list_keywords:
        # Use word boundaries for more precise matching of keywords
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.add(skill.capitalize() if not skill.isupper() else skill)

    # Method 2: NER for potential technologies (ORG, PRODUCT often catch tech names)
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"]:
            ent_text_lower = ent.text.lower()
            # Check if the NER entity is in our skill list or a known variant
            if ent_text_lower in skills_list_keywords:
                 found_skills.add(ent_text_lower.capitalize() if not ent_text_lower.isupper() else ent_text_lower)
            # Could add more logic here to accept ORG/PRODUCT if they look like tech, even if not in list.
            # For example, if it contains "SDK", "API", "Framework", etc.
            elif any(tech_kw in ent_text_lower for tech_kw in ['sdk', 'api', 'framework', 'platform', 'library']):
                 found_skills.add(ent.text.strip())


    # Method 3: Look for specific skill sections
    skill_section_regex = re.compile(
        r"(skills|technical skills|proficiencies|technologies|technical proficiencies|core competencies)[\s:]*\n((?:.|\n)+?)(?=\n\s*(?:Education|Experience|Projects|Awards)|$)",
        re.IGNORECASE
    )
    section_matches = skill_section_regex.finditer(text) # Use original text for spaCy processing if needed
    for match in section_matches:
        section_content = match.group(2).strip()
        section_doc = nlp(section_content) # Process only the section with spaCy
        for token in section_doc: # Lemmatized check against keywords
            if token.lemma_.lower() in skills_list_keywords:
                 found_skills.add(token.lemma_.capitalize() if not token.lemma_.isupper() else token.lemma_)
        for skill_phrase in skills_list_keywords: # Check for multi-word skills in the section text
            if re.search(r'\b' + re.escape(skill_phrase) + r'\b', section_content.lower()):
                 found_skills.add(skill_phrase.capitalize() if not skill_phrase.isupper() else skill_phrase)
        # Add comma/bullet separated items from the section as potential skills
        items_in_section = re.split(r'[,;\n•*-]\s*', section_content)
        for item in items_in_section:
            item_clean = item.strip()
            if 1 < len(item_clean) < 30 : # Heuristic for skill length
                # Optional: Add only if it looks like a skill (e.g., capitalized, contains certain characters)
                # For now, adding if it's a reasonable length.
                found_skills.add(item_clean)

    return sorted(list(s for s in found_skills if s)) # Filter out any empty strings

def _extract_section_text(pattern: re.Pattern, text: str) -> Optional[str]:
    """Helper to extract text for a given section pattern."""
    match = pattern.search(text)
    if match:
        # Find where this section ends by looking for the start of the next major section
        section_text = match.group(0) # The whole match including the header
        content_after_header = text[match.end():]
        next_section_match = SECTION_ENDERS_PATTERN.search(content_after_header)
        if next_section_match:
            return section_text + content_after_header[:next_section_match.start()]
        else: # Section is the last one
            return section_text + content_after_header
    return None

def parse_summary(doc: spacy.tokens.Doc, text: str) -> Optional[str]:
    """Parses the summary/objective section."""
    summary_text_block = _extract_section_text(SUMMARY_SECTION_PATTERN, text)
    if summary_text_block:
        # Remove the header itself from the extracted block
        header_match = SUMMARY_SECTION_PATTERN.match(summary_text_block) # Match from start
        if header_match:
            return summary_text_block[header_match.end():].strip()
    return None


def _parse_single_education_entry(entry_text: str) -> Optional[Dict[str, str]]:
    """Helper function to parse a single education entry block."""
    entry_text = entry_text.strip()
    if not entry_text or len(entry_text) < 10: return None

    entry_doc = nlp(entry_text)
    # Regex patterns should be pre-compiled or defined globally for efficiency
    degree_pattern = re.compile(r'\b(?:B\.?S\.?c?|M\.?S\.?c?|Ph\.?D|M\.?B\.?A|B\.?A\.?|Associate|Diploma|Certificate|Bachelor(?: of| of Science| of Arts)?|Master(?: of| of Science| of Arts)?|Doctor(?: of Philosophy)?)\b(?: in| of)?\s*([\w\s,.&()-]+)', re.IGNORECASE)
    date_pattern = re.compile(r'\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?(?:\d{4}|\d{2})\b(?:[-\s/to]+\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?(?:\d{4}|\d{2})\b|\bPresent\b|\bCurrent\b)?', re.IGNORECASE)

    degree_match = degree_pattern.search(entry_text)
    degree = degree_match.group(1).strip().rstrip(',') if degree_match and degree_match.group(1) else (degree_match.group(0) if degree_match else None)

    institution, date_str = None, None
    for ent in entry_doc.ents:
        if ent.label_ == "ORG" and not institution:
            if any(kw in ent.text.lower() for kw in ['university', 'college', 'institute', 'school', 'academy']):
                institution = ent.text.strip()
        elif ent.label_ == "DATE" and not date_str:
            if date_pattern.search(ent.text): date_str = ent.text.strip()

    if not date_str:
        date_match_fallback = date_pattern.search(entry_text)
        if date_match_fallback: date_str = date_match_fallback.group(0).strip()

    # Heuristic for institution if not found by NER
    if not institution and (degree or date_str):
        # Attempt to find text between degree and date, or just capitalized phrases.
        # This remains a complex heuristic.
        # For simplicity, if degree is found, assume text after it could be institution.
        # This needs more refinement for real-world accuracy.
        if degree_match:
            remaining_text = entry_text[degree_match.end():].strip()
            if date_str: # If date is also found, take text between degree and date
                date_idx = remaining_text.lower().find(date_str.lower())
                if date_idx != -1: remaining_text = remaining_text[:date_idx].strip()

            # Find capitalized words/phrases in remaining text
            potential_inst = re.findall(r'([A-Z][\w\s.&\'()-]+(?:University|College|Institute|School|Academy)?\b)', remaining_text)
            if potential_inst: institution = potential_inst[0].strip().rstrip(',') # Take first likely candidate
            elif remaining_text and len(remaining_text.split()) < 7 : institution = remaining_text.strip().rstrip(',')


    if degree or institution or date_str:
        return {'degree': degree or "N/A", 'institution': institution or "N/A", 'date': date_str or "N/A"}
    return None

def parse_education(doc: spacy.tokens.Doc, text: str) -> List[Dict[str, str]]:
    """Parses education details from the resume text."""
    education_entries = []
    education_text_block = _extract_section_text(EDUCATION_SECTION_PATTERN, text)
    if not education_text_block: return education_entries

    # Remove the header itself from the extracted block
    header_match = EDUCATION_SECTION_PATTERN.match(education_text_block)
    if header_match: education_text_block = education_text_block[header_match.end():].strip()

    # Split entries by double newlines or lines that look like a new degree/institution
    potential_entries = re.split(r'\n\s*\n+|\n(?=\s*(?:[A-Z][\w\s,.&()-]+\s*(?:University|College|Institute|School|Academy)|(?:B\.?S|M\.?S|Ph\.?D|Bachelor|Master|Doctor)))', education_text_block)

    for entry_text in potential_entries:
        if entry_text.strip():
            try:
                parsed_entry = _parse_single_education_entry(entry_text)
                if parsed_entry: education_entries.append(parsed_entry)
            except Exception as e: print(f"Error parsing education entry: '{entry_text[:50]}...': {e}")
    return education_entries


def _parse_single_experience_entry(entry_text: str) -> Optional[Dict[str, str]]:
    """Helper function to parse a single experience entry block."""
    entry_text = entry_text.strip()
    if not entry_text or len(entry_text) < 15: return None # Min length for a meaningful entry

    job_title, company, date_range, description = None, None, None, []
    lines = entry_text.split('\n')

    # Date extraction (try from any line, but often top or bottom)
    job_date_pattern_local = re.compile(JOB_DATE_PATTERN.pattern, JOB_DATE_PATTERN.flags) # Ensure it's compiled
    for i, line in enumerate(lines):
        date_match = job_date_pattern_local.search(line)
        if date_match:
            date_range = date_match.group(0).strip()
            # Remove date part from line to avoid re-parsing as title/company
            lines[i] = job_date_pattern_local.sub('', line).strip()
            break # Assume one date range per entry for simplicity

    # Title and Company (often in the first few non-date lines)
    # This is highly heuristic.
    processed_header_lines = 0
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or line_stripped == date_range: # Skip empty or already processed date lines
            processed_header_lines += 1
            continue
        if i > 2 and (job_title or company): # Assume header is within first 3 lines usually
            break

        # Try to match "Title at Company" or "Title, Company" or "Title - Company"
        title_company_match = re.match(r'([\w\s.&\'()/-]+?)\s*(?:at|@|,|-)\s*([\w\s.&\'()/-]+)', line_stripped, re.IGNORECASE)
        if title_company_match and not job_title and not company:
            job_title = title_company_match.group(1).strip()
            company = title_company_match.group(2).strip()
            processed_header_lines +=1
            break

        # If no clear separator, use NER on the line
        line_doc = nlp(line_stripped)
        current_line_orgs = [ent.text.strip() for ent in line_doc.ents if ent.label_ == "ORG"]

        if not company and current_line_orgs:
            company = current_line_orgs[0] # Take first ORG as company
            # Assume rest of the line (if any) is job title
            if not job_title: job_title = line_stripped.replace(company, "").strip().rstrip(',-')
        elif not job_title: # No company found yet on this line via NER, assume line is title
            job_title = line_stripped.strip().rstrip(',-')

        processed_header_lines +=1
        if job_title and company: break # Found both

    # Description lines (remaining lines)
    description_lines = [line.strip() for line in lines[processed_header_lines:] if line.strip() and line.strip() != date_range]
    description = "\n".join(description_lines).strip()

    if job_title or company or date_range:
        return {
            'job_title': job_title or "N/A", 'company': company or "N/A",
            'date_range': date_range or "N/A", 'description': description or "N/A"
        }
    return None

def parse_experience(doc: spacy.tokens.Doc, text: str) -> List[Dict[str, str]]:
    """Parses work experience details."""
    experience_entries = []
    experience_text_block = _extract_section_text(EXPERIENCE_SECTION_PATTERN, text)
    if not experience_text_block: return experience_entries

    header_match = EXPERIENCE_SECTION_PATTERN.match(experience_text_block)
    if header_match: experience_text_block = experience_text_block[header_match.end():].strip()

    # Split entries: two+ newlines OR newline followed by potential job title/company (often capitalized) OR date range
    entry_splits = re.split(
        r'\n\s*\n\s*\n*|\n(?=\s*(?:[A-Z][\w\s.,&\'()/-]{5,}\s*(?:at|@|,|-|\|)?\s*[A-Z][\w\s.,&\'()/-]{2,}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b|\d{4}\s*-\s*\d{4}))',
        experience_text_block
    )
    for entry_text in entry_splits:
        if entry_text.strip():
            try:
                parsed_entry = _parse_single_experience_entry(entry_text)
                if parsed_entry: experience_entries.append(parsed_entry)
            except Exception as e: print(f"Error parsing experience entry: '{entry_text[:50]}...': {e}")

    return experience_entries

# --- Main Parsing Orchestrator ---
def parse_resume_text(text: str) -> Dict[str, Any]:
    """Main function to parse resume text."""
    if not text or not isinstance(text, str):
        print("Invalid input text for parsing: Must be a non-empty string.")
        return RB_FIELDS_DEFINITIONS_DEFAULT.copy() # Ensure a default structure

    doc = nlp(text)
    text_lower = text.lower()
    text_lines = text.split('\n')

    # Initialize with default values from a constant to ensure consistency
    # (Assuming RB_FIELDS_DEFINITIONS_DEFAULT is defined similarly to RB_FIELDS_DEFINITIONS in app)
    # For now, defining a local default:
    parsed_data = {
        "name": "N/A", "email": "N/A", "phone": "N/A",
        "skills": [], "summary": "N/A",
        "education": [], "experience": []
    }

    try:
        parsed_data["name"] = parse_name(doc, text_lines) or "N/A"
        parsed_data["email"] = parse_email(text) or "N/A"
        parsed_data["phone"] = parse_phone(text) or "N/A"
        parsed_data["skills"] = parse_skills(doc, text_lower) # Returns list, empty if none
        parsed_data["summary"] = parse_summary(doc, text) or "N/A"

        parsed_data["education"] = parse_education(doc, text)
        parsed_data["experience"] = parse_experience(doc, text)

    except Exception as e:
        print(f"Critical error during resume parsing: {e}")
        # Ensure structure is preserved even on critical error
        for key, default_val_type in [("name",str), ("email",str), ("phone",str), ("skills",list), ("summary",str), ("education",list), ("experience",list)]:
            if key not in parsed_data or not isinstance(parsed_data[key], default_val_type):
                parsed_data[key] = "N/A" if default_val_type == str else []

    # Ensure list fields are lists, even if empty, and string fields are strings.
    # And add placeholder dicts if education/experience are empty for consistent UI handling in Streamlit.
    if not parsed_data["skills"]: parsed_data["skills"] = ["N/A"] # If empty list, make it ["N/A"]
    if not parsed_data["education"]: parsed_data["education"] = [{'degree': 'N/A', 'institution': 'N/A', 'date': 'N/A'}]
    if not parsed_data["experience"]: parsed_data["experience"] = [{'job_title': 'N/A', 'company': 'N/A', 'date_range': 'N/A', 'description': 'N/A'}]

    return parsed_data

# --- Test Section (Example Usage) ---
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

Lead Software Developer
QuantumLeap Tech, Remote | Jan 2020 – Present
- Spearheaded the development of a new microservices-based platform using Python, Flask, Docker, and Kubernetes on AWS.
- Managed a team of 6 software engineers, providing mentorship and technical guidance.
- Reduced system latency by 25% through performance optimization and architectural improvements.

Software Engineer at AlphaBeta Solutions | June 2015 - Dec 2019
- Developed and maintained scalable web applications using Java, Spring Boot, and PostgreSQL.
- Collaborated with cross-functional teams to define project requirements and deliver features.

Education

Massachusetts Institute of Technology (MIT)
M.S. in Computer Science | May 2015
Thesis: Efficient Algorithms for Large-Scale Data Processing.

Stanford University, CA
Bachelor of Science (B.S.) in Computer Engineering, Minor in Mathematics. June 2011. GPA: 3.9/4.0.

Technical Skills: Python (Expert), Java (Expert), C++, SQL, JavaScript, TypeScript, AWS, Azure, Docker, Kubernetes, Agile, Scrum.
    """

    print("--- Running Resume Parser in Test Mode ---")
    if nlp.meta.get('lang') == 'en' and 'ner' in nlp.pipe_names:
        parsed_data = parse_resume_text(sample_text_for_testing)
        import json
        print(json.dumps(parsed_data, indent=2))
    else:
        print("Skipping test: spaCy model 'en_core_web_sm' not fully loaded or functional.")
    pass
