import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
# Assuming slm_module.parser defines EXPECTED_FIELDS or similar structure for parsed_resume
# from slm_module.parser import EXPECTED_FIELDS # Or access it via a shared model definition

# --- Constants & Basic Configuration ---
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# Common keywords that might indicate skill sections or important parts of a job description
JOB_DESC_KEYWORD_PATTERNS = {
    "responsibilities": re.compile(r"(Responsibilities|What you'll do|Your role):", re.IGNORECASE),
    "qualifications": re.compile(r"(Qualifications|Requirements|Skills|Experience|Who you are|Ideal candidate):", re.IGNORECASE),
    "preferred": re.compile(r"(Preferred|Bonus points|Nice to have):", re.IGNORECASE),
}

# --- Web Scraping ---
def scrape_job_description_from_url(url: str) -> Optional[str]:
    """
    Scrapes the main textual content from a job description URL.
    This is a very basic scraper and might need significant improvement for different job sites.
    """
    try:
        response = requests.get(url, headers=DEFAULT_REQUEST_HEADERS, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, 'html.parser')

        # Attempt to find common tags/attributes for job descriptions
        # This is highly heuristic and will vary widely between job sites.
        # Common selectors: 'div.job-description', 'article.job-description', id="jobDescription"
        # For a more generic approach, we can try to remove nav, footer, header, script, style
        # and then get text from main content areas.

        for tag_name in ['script', 'style', 'nav', 'footer', 'header', 'aside']:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Try some common selectors
        potential_containers = [
            soup.find('div', class_=re.compile(r"job-description|jobdescription|description|jobDetails|jobdetails", re.I)),
            soup.find('article', class_=re.compile(r"job-description|jobdescription", re.I)),
            soup.find(id=re.compile(r"jobDescription|jobdescription", re.I)),
            soup.find('main'), # Fallback to main content
            soup.body # Fallback to body
        ]

        text_content = ""
        for container in potential_containers:
            if container:
                text_content = container.get_text(separator='\n', strip=True)
                if len(text_content) > 300: # Assume a reasonable length for a job desc
                    break

        return text_content.strip() if text_content.strip() else None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        print(f"Error scraping job description from {url}: {e}")
        return None

# --- Text Processing & Keyword Extraction ---
def extract_keywords_from_text(text: str, min_keyword_length: int = 3, top_n: int = 50) -> List[str]:
    """
    A very simple keyword extraction method.
    Extracts potential keywords (alphanumeric, possibly with hyphens/dots) from text.
    This is not true NLP keyword extraction but a basic heuristic.
    """
    if not text:
        return []

    # Remove common punctuation, convert to lower, split into words
    words = re.findall(r'\b[a-zA-Z0-9.-]+\b', text.lower())

    # Filter out very short words and common stop words (very basic list)
    stop_words = set(['and', 'the', 'is', 'in', 'it', 'to', 'a', 'of', 'for', 'on', 'with', 'as', 'at', 'by'])
    keywords = [word for word in words if len(word) >= min_keyword_length and word not in stop_words]

    # Simple frequency count (can be improved with TF-IDF later if needed)
    from collections import Counter
    keyword_counts = Counter(keywords)

    # Return the most common keywords
    return [kw for kw, count in keyword_counts.most_common(top_n)]

# --- Comparison Logic ---
def compare_resume_to_job_description(
    parsed_resume_data: Dict[str, Any],
    job_description_text: str
) -> Dict[str, Any]:
    """
    Compares extracted resume data with job description text.
    Highlights matching skills and potentially missing keywords.
    `parsed_resume_data` is expected to be the output from the SLM parser.
    """
    comparison_results = {
        "matching_skills": [],
        "missing_skills_from_jd": [],
        "job_summary_keywords": [],
        "match_score_heuristic": 0.0 # Very basic score
    }

    if not parsed_resume_data or not job_description_text:
        return comparison_results

    # Extract keywords from job description
    jd_keywords_set = set(extract_keywords_from_text(job_description_text))
    comparison_results["job_summary_keywords"] = sorted(list(jd_keywords_set))[:20] # Show some JD keywords

    resume_skills = parsed_resume_data.get("skills", [])
    if not isinstance(resume_skills, list): resume_skills = []

    # Normalize resume skills to lower case for comparison
    resume_skills_lower = set([str(skill).lower() for skill in resume_skills if skill])

    # Find matching skills
    matching_skills = []
    for r_skill_lower in resume_skills_lower:
        # Direct match or if the resume skill is a substring of a JD keyword (e.g., "react" in "react.js")
        if r_skill_lower in jd_keywords_set or any(r_skill_lower in jd_kw for jd_kw in jd_keywords_set):
            # Find original casing from resume_skills if possible
            original_skill = next((s for s in resume_skills if str(s).lower() == r_skill_lower), r_skill_lower)
            matching_skills.append(original_skill)

    comparison_results["matching_skills"] = sorted(list(set(matching_skills)))

    # Identify skills mentioned in JD that are not in resume (based on JD keywords)
    # This is very heuristic as jd_keywords are not necessarily "skills"
    potential_jd_skills = jd_keywords_set
    missing_skills = [jd_kw for jd_kw in potential_jd_skills if jd_kw not in resume_skills_lower and not any(r_skill in jd_kw for r_skill in resume_skills_lower)]
    comparison_results["missing_skills_from_jd"] = sorted(list(set(missing_skills)))[:15] # Limit for display

    # Basic match score: (Number of matching skills / Number of unique skills in resume + unique keywords in JD)
    # This is a very naive score and can be improved significantly.
    if resume_skills_lower or jd_keywords_set:
        total_unique_terms = len(resume_skills_lower.union(jd_keywords_set))
        if total_unique_terms > 0:
            comparison_results["match_score_heuristic"] = round((len(matching_skills) / total_unique_terms) * 100, 2)
        else:
            comparison_results["match_score_heuristic"] = 0.0 if not matching_skills else 100.0


    # Potential further analysis:
    # - Check for matching keywords in experience descriptions.
    # - Years of experience matching (requires parsing numbers and terms like "X+ years").
    # - Education level matching.

    return comparison_results

# --- Main for Testing ---
if __name__ == '__main__':
    print("--- Job Analyzer Logic Test ---")

    # Test scraping (use a known, relatively stable job posting if possible, or mock)
    # test_job_url = "URL_OF_A_SAMPLE_JOB_POSTING" # Replace with a real URL for testing
    # print(f"Attempting to scrape: {test_job_url}")
    # job_text = scrape_job_description_from_url(test_job_url)
    # if job_text:
    #     print(f"Successfully scraped content (first 500 chars):\n{job_text[:500]}\n...")
    #     jd_keywords_example = extract_keywords_from_text(job_text)
    #     print(f"Extracted JD Keywords (sample): {jd_keywords_example[:10]}")
    # else:
    #     print(f"Failed to scrape {test_job_url}")

    # Test comparison with dummy data
    sample_resume_data = {
        "name": "Jane Doe",
        "skills": ["Python", "Machine Learning", "Data Analysis", "Communication", "React"],
        "experience": [
            {"job_title": "Data Scientist", "description": "Developed machine learning models using Python and Scikit-learn."},
            {"job_title": "Software Engineer", "description": "Built web applications with React and Node.js."}
        ]
        # ... other fields from SLM
    }

    sample_job_description = """
    Job Title: Senior Python Developer (Machine Learning)
    Location: San Francisco, CA

    We are looking for an experienced Python Developer with a strong background in Machine Learning.
    The ideal candidate will have experience with Scikit-learn, TensorFlow, or PyTorch.
    Responsibilities include designing and implementing ML models, and working with large datasets.
    Required Skills: Python, Machine Learning, SQL, Data Analysis, Problem Solving.
    Preferred: Experience with AWS, Docker, and Agile methodologies. Knowledge of React is a plus.
    """
    print("\n--- Testing Comparison Logic ---")
    print("Sample Resume Skills:", sample_resume_data["skills"])
    print("Sample JD Text (snippet):", sample_job_description[:100] + "...")

    comparison = compare_resume_to_job_description(sample_resume_data, sample_job_description)
    import json
    print("\nComparison Results:")
    print(json.dumps(comparison, indent=2))

    # Test with empty/None inputs
    empty_comparison = compare_resume_to_job_description(None, None)
    print("\nComparison with empty inputs:")
    print(json.dumps(empty_comparison, indent=2))

    no_resume_skills = {"name": "Test"}
    comp_no_resume_skills = compare_resume_to_job_description(no_resume_skills, sample_job_description)
    print("\nComparison with no resume skills:")
    print(json.dumps(comp_no_resume_skills, indent=2))
