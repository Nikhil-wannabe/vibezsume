import PyPDF2
import docx
import re
import spacy
from spacy.matcher import Matcher

# Load the small English model for spacy
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    # This might happen in environments where the model needs to be downloaded first.
    # The calling environment (like the bash session) should handle this.
    print("Spacy model 'en_core_web_sm' not found. Please download it by running: python -m spacy download en_core_web_sm")
    # Fallback to a blank English model if download fails or isn't done, though NER will be limited.
    nlp = spacy.blank("en")


# --- Text Extraction (same as before) ---
def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

# --- Enhanced Parsing Logic ---

def parse_name(doc):
    """Parses name using spacy NER and patterns."""
    matcher = Matcher(nlp.vocab)
    # Pattern for full names (two capitalized words)
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
    matcher.add('NAME', [pattern])
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text
    # Fallback: Check for PERSON entities if pattern fails
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None # Fallback if nothing found

def parse_email(text):
    """Parses email using regex."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def parse_phone(text):
    """Parses phone number using regex."""
    # More comprehensive phone pattern
    phone_pattern = r"(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}"
    match = re.search(phone_pattern, text)
    return match.group(0) if match else None

def parse_skills(doc, text_lower):
    """Parses skills using a predefined list and section headers."""
    skills_list = [
        'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'sql', 'nosql', 'mongodb', 'postgresql',
        'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring boot',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
        'machine learning', 'deep learning', 'nlp', 'natural language processing', 'computer vision',
        'data analysis', 'data science', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
        'agile', 'scrum', 'jira', 'git', 'restful apis', 'microservices', 'html', 'css',
        'communication', 'teamwork', 'problem solving', 'leadership', 'project management'
    ]
    found_skills = set()

    # Method 1: Keyword matching in the whole document
    for skill in skills_list:
        if skill in text_lower:
            found_skills.add(skill.capitalize())

    # Method 2: Look for specific skill sections
    # This regex looks for common skill section headers and captures the text under them
    # until a known next section header or a significant break.
    skill_section_pattern = re.compile(
        r"(skills|technical skills|proficiencies|technologies|technical proficiencies)[\s:]*\n((?:[ \t]*(?:[\w\s,+#./()&'-]+)(?:\n|$))+)",
        re.IGNORECASE
    )
    matches = skill_section_pattern.finditer(text_lower)
    for match in matches:
        section_content = match.group(2).strip()
        # Tokenize the section content and check for skills
        section_doc = nlp(section_content)
        for token in section_doc:
            if token.lemma_.lower() in skills_list:
                 found_skills.add(token.lemma_.capitalize())
        # Also check for multi-word skills within this section
        for skill in skills_list:
            if skill in section_content:
                 found_skills.add(skill.capitalize())

    # Method 3: Using spaCy's PhraseMatcher for more complex skill phrases (if needed)
    # For now, regex and keyword list should cover a lot.

    return sorted(list(found_skills))


def parse_education(doc, text):
    """Parses education details using regex and NER."""
    education_entries = []

    # Regex to find common education section headers
    education_section_pattern = re.compile(
        r"(education|academic background|qualifications)[\s:]*\n((?:.|\n)+?)(?=\n(?:experience|skills|projects|awards|publications|references|technical skills)|$)",
        re.IGNORECASE
    )
    section_match = education_section_pattern.search(text)

    if not section_match:
        return education_entries

    education_text = section_match.group(2)

    # Split the education section into potential entries (e.g., by newline or bullet points)
    # This is a heuristic and might need refinement.
    potential_entries = re.split(r'\n\n+|\n\s*(?:•|-)\s*|\n(?=[A-Z][^a-z])', education_text.strip())

    degree_pattern = r'\b(?:B\.?S\.?c?|M\.?S\.?c?|Ph\.?D|M\.?B\.?A|B\.?A\.?|Bachelor(?: of| of Science| of Arts)?|Master(?: of| of Science| of Arts)?|Doctor(?: of Philosophy)?)\b(?: in)?\s*([\w\s,]+)'
    date_pattern = r'\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?\d{4}\b|\b\d{4}\s*-\s*\d{4}\b|\bPresent\b'

    for entry_text in potential_entries:
        if not entry_text.strip() or len(entry_text.strip()) < 10: # Skip very short lines
            continue

        entry_doc = nlp(entry_text)
        degree_match = re.search(degree_pattern, entry_text, re.IGNORECASE)

        degree = degree_match.group(1).strip() if degree_match else None
        if degree_match and not degree : # if "B.S. in" was matched, group(1) is the field
             degree = degree_match.group(0).strip()


        institution = None
        date_str = None

        for ent in entry_doc.ents:
            if ent.label_ == "ORG" and not institution:
                # Check if it's a known university keyword, very basic
                if any(uni_kw in ent.text.lower() for uni_kw in ['university', 'college', 'institute']):
                    institution = ent.text
            elif ent.label_ == "DATE" and not date_str:
                 # Prioritize dates found by NER if they look like graduation years/ranges
                if re.search(date_pattern, ent.text):
                    date_str = ent.text

        # Fallback regex for dates if NER misses them
        if not date_str:
            date_match = re.search(date_pattern, entry_text)
            if date_match:
                date_str = date_match.group(0)

        # Fallback for institution (if not found by NER or if NER is too broad)
        if not institution and degree:
            # Try to get text after degree and before date as institution
            # This is very heuristic
            possible_institution_text = entry_text
            if degree_match:
                possible_institution_text = possible_institution_text[degree_match.end():]
            if date_str and date_match: #if date was found by regex
                possible_institution_text = possible_institution_text[:date_match.start()]

            # Simplistic: assume the longest capitalized phrase is the institution
            # This needs a lot of improvement.
            inst_candidates = re.findall(r'((?:[A-Z][\w\s.-]+)+)', possible_institution_text)
            if inst_candidates:
                institution = max(inst_candidates, key=len).strip().replace('\n',' ')
                if len(institution.split()) > 5: # Heuristic: too long for just institution name
                    institution = " ".join(institution.split()[:5]) # take first 5 words


        if degree or institution or date_str:
            education_entries.append({
                'degree': degree.strip().rstrip(',') if degree else "N/A",
                'institution': institution.strip().rstrip(',') if institution else "N/A",
                'date': date_str.strip() if date_str else "N/A"
            })

    return education_entries


def parse_experience(doc, text):
    """Parses work experience details using regex and NER."""
    experience_entries = []

    # Regex to find common experience section headers
    experience_section_pattern = re.compile(
        r"(experience|work experience|professional experience|employment history)[\s:]*\n((?:.|\n)+?)(?=\n(?:education|skills|projects|awards|publications|references)|$)",
        re.IGNORECASE
    )
    section_match = experience_section_pattern.search(text)

    if not section_match:
        return experience_entries

    experience_text = section_match.group(2)

    # Attempt to split into distinct job entries. This is highly heuristic.
    # Looks for patterns like "Job Title at Company Name" or date ranges followed by text.
    # This regex is complex and will need significant testing and refinement.
    job_entry_splits = re.split(r'\n\n+(?=[A-Z])|\n(?=\s*(?:[A-Z][\w\s.&'-]+?)\s*(?:,|at|@|-)\s*(?:[A-Z][\w\s.&'-]+))|\n(?=\s*\d{4}\s*-\s*(?:\d{4}|Present|Current))', experience_text.strip())

    date_pattern = r'\b(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?\d{4}\s*(?:-|to|–|—)\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s*)?(?:\d{4}|Present|Current)\b'

    for entry_text in job_entry_splits:
        entry_text = entry_text.strip()
        if not entry_text or len(entry_text) < 20: # Skip very short segments
            continue

        entry_doc = nlp(entry_text)
        job_title = None
        company = None
        date_range = None
        description_lines = []

        # Try to find date range first
        date_match = re.search(date_pattern, entry_text, re.IGNORECASE)
        if date_match:
            date_range = date_match.group(0)
            # Remove date from entry_text to simplify title/company extraction
            entry_text_no_date = entry_text.replace(date_range, "").strip()
            entry_doc_no_date = nlp(entry_text_no_date)
        else:
            entry_doc_no_date = entry_doc


        # NER for Company (ORG) and potentially Job Title (heuristic)
        # This is tricky because job titles are not standard NER categories.
        # We might look for nouns/propns before an ORG or specific keywords.

        # Heuristic: first line or prominent capitalized phrase as title/company
        lines = entry_text_no_date.split('\n')
        first_line_processed = False
        if lines:
            first_line = lines[0].strip()
            # Check for "Title at Company" or "Title, Company"
            match_title_company = re.match(r'([\w\s.&\'/-]+?)\s*(?:at|@|,)\s*([\w\s.&\'/-]+)', first_line)
            if match_title_company:
                job_title = match_title_company.group(1).strip()
                company = match_title_company.group(2).strip()
                first_line_processed = True
            else: # Fallback for first line as potential title if no clear company separator
                 # NER on the first line
                first_line_doc = nlp(first_line)
                for ent in first_line_doc.ents:
                    if ent.label_ == "ORG" and not company:
                        company = ent.text
                if not company: # If no ORG, assume first part is title, rest might be company
                    # This is very weak, might need a list of common job keywords (Engineer, Manager, etc.)
                    # For now, if there's a comma, split, otherwise take it as title
                    if ',' in first_line:
                        parts = first_line.split(',', 1)
                        job_title = parts[0].strip()
                        company = parts[1].strip() if len(parts) > 1 else None
                    else:
                        job_title = first_line # Could be just title, or title and company unparsed
                first_line_processed = True


        # Try to find company using NER on the whole entry_doc_no_date if not found yet
        if not company:
            for ent in entry_doc_no_date.ents:
                if ent.label_ == "ORG":
                    company = ent.text
                    break # Take the first ORG

        # Description: usually bullet points or paragraphs following the title/company/date.
        # Start collecting description from the line after title/company if processed, or all lines.
        start_desc_line = 1 if first_line_processed and (job_title or company) else 0
        for i in range(start_desc_line, len(lines)):
            line = lines[i].strip()
            if line:
                 # Remove company name from description if it was misidentified as part of a line
                if company and company in line and len(line.replace(company, "").strip()) < 5: # if line is mostly company name
                    continue
                if date_range and date_range in line and len(line.replace(date_range, "").strip()) < 5:
                    continue
                description_lines.append(line)

        description = "\n".join(description_lines).strip()
        # Further clean up description - remove job title/company if they are repeated at the start
        if job_title and description.startswith(job_title):
            description = description[len(job_title):].strip()
        if company and description.startswith(company):
            description = description[len(company):].strip()


        if job_title or company or date_range:
            experience_entries.append({
                'job_title': job_title.strip() if job_title else "N/A",
                'company': company.strip() if company else "N/A",
                'date_range': date_range.strip() if date_range else "N/A",
                'description': description if description else "N/A"
            })

    return experience_entries

def parse_summary(doc, text):
    """Parses summary using section headers."""
    summary_match = re.search(
        r"(summary|objective|profile|about me|professional profile|personal statement)\s*?\n([\s\S]+?)(?=\n\s*(?:experience|skills|education|projects)|$)",
        text, re.IGNORECASE
    )
    return summary_match.group(2).strip() if summary_match else None


def parse_resume_text(text):
    """
    Main function to parse extracted text to find structured data.
    Uses spaCy for NLP tasks.
    """
    if not text:
        return {}

    doc = nlp(text) # Process the whole text with spaCy once
    text_lower = text.lower() # For case-insensitive keyword searches

    resume_data = {
        "name": parse_name(doc) or (text.split('\n')[0].strip() if text.split('\n')[0].strip() else "N/A"), # Fallback
        "email": parse_email(text) or "N/A",
        "phone": parse_phone(text) or "N/A",
        "skills": parse_skills(doc, text_lower) or ["N/A"],
        "summary": parse_summary(doc, text) or "N/A",
        "education": parse_education(doc, text) or [], # Expect list of dicts
        "experience": parse_experience(doc, text) or [], # Expect list of dicts
    }

    # If education/experience are empty, add a placeholder dict for display
    if not resume_data["education"]:
        resume_data["education"] = [{'degree': 'N/A', 'institution': 'N/A', 'date': 'N/A'}]
    if not resume_data["experience"]:
        resume_data["experience"] = [{'job_title': 'N/A', 'company': 'N/A', 'date_range': 'N/A', 'description': 'N/A'}]


    return resume_data

if __name__ == '__main__':
    # Keep this for local testing if needed.
    # You would create a dummy text variable or load from a test file.
    sample_text_for_testing = """
John Doe
john.doe@example.com | (123) 456-7890 | linkedin.com/in/johndoe

Summary
Experienced Software Engineer with a demonstrated history of working in the computer software industry. Skilled in Python, Java, SQL, and Agile Methodologies. Strong engineering professional with a Bachelor of Science (B.S.) focused in Computer Science from University of Example.

Experience
Senior Software Engineer at Tech Solutions Inc. | Jan 2021 - Present
- Developed and maintained web applications using Python and Django.
- Led a team of 5 engineers in an Agile environment.
- Implemented microservices architecture for new product features.

Software Engineer at Innovatech Ltd. | Jun 2018 - Dec 2020
- Contributed to the development of a large-scale data processing system.
- Worked with Java, Spring Boot, and PostgreSQL.
- Wrote unit and integration tests to ensure code quality.

Education
University of Example | Aug 2014 - May 2018
Bachelor of Science in Computer Science
GPA: 3.8/4.0

Technical Skills
Languages: Python, Java, SQL, JavaScript
Frameworks: Django, Spring Boot, React
Databases: PostgreSQL, MongoDB
Tools: Git, Docker, AWS

Projects
Personal Portfolio Website (React, Node.js)
Resume Parser (Python, spaCy) - This very project!
    """

    print("--- Running Parser in Main (Test Mode) ---")
    if nlp.meta['name'] == 'core_web_sm' or nlp.meta.get('lang') == 'en': # Check if a valid model is loaded
        parsed_data = parse_resume_text(sample_text_for_testing)
        print("\n--- Parsed Data ---")
        import json
        print(json.dumps(parsed_data, indent=2))
    else:
        print("Skipping test run as spaCy model might not be fully loaded for parsing.")

    # Example for testing education section alone:
    # test_edu_text = """
    # EDUCATION
    # Stanford University, Stanford, CA May 2020
    # M.S. in Computer Science, GPA: 3.9/4.0
    # University of California, Berkeley Aug 2016 - May 2018
    # B.A. in Cognitive Science, Minor in Computer Science
    # Relevant Coursework: Data Structures, Algorithms, Machine Learning, AI.
    # """
    # edu_doc = nlp(test_edu_text)
    # parsed_edu = parse_education(edu_doc, test_edu_text)
    # print("\n--- Parsed Education (Test) ---")
    # print(json.dumps(parsed_edu, indent=2))

    # Example for testing experience section alone:
    # test_exp_text = """
    # WORK EXPERIENCE
    # Google, Mountain View, CA Jan 2021 – Present
    # Software Engineer
    # • Worked on the Search team to improve query understanding.
    # • Developed features using C++ and Python.
    # Acme Corp, Remote Dec 2018 - Nov 2020
    # Junior Developer
    # - Responsible for front-end development using React.
    # - Collaborated with designers to implement UI mockups.
    # """
    # exp_doc = nlp(test_exp_text)
    # parsed_exp = parse_experience(exp_doc, test_exp_text)
    # print("\n--- Parsed Experience (Test) ---")
    # print(json.dumps(parsed_exp, indent=2))
    pass
