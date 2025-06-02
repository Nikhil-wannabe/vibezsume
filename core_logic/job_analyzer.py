"""
Core logic for analyzing job descriptions and comparing them against resume data.

This module provides functionalities to:
1. Scrape job description text from a given URL.
2. Extract potential keywords from text (job descriptions or resume sections).
3. Compare a parsed resume with a job description to find matching skills and suggest areas for improvement.

The methods used are often heuristic and may require tuning for optimal performance across various
job sites and resume formats.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from collections import Counter # Moved import to top level for clarity

# Assuming slm_module.parser defines EXPECTED_FIELDS or similar structure for parsed_resume
# from slm_module.parser import EXPECTED_FIELDS # Or access it via a shared model definition

# --- Constants & Basic Configuration ---

# Standard headers to mimic a browser request, reducing likelihood of being blocked.
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Regex patterns to identify common sections within a job description.
# These help in potentially segmenting or prioritizing parts of the JD text, though not fully utilized yet.
JOB_DESC_KEYWORD_PATTERNS = {
    "responsibilities": re.compile(r"(Responsibilities|What you'll do|Your role):", re.IGNORECASE),
    "qualifications": re.compile(r"(Qualifications|Requirements|Skills|Experience|Who you are|Ideal candidate):", re.IGNORECASE),
    "preferred": re.compile(r"(Preferred|Bonus points|Nice to have):", re.IGNORECASE),
}

# --- Web Scraping ---
def scrape_job_description_from_url(url: str) -> Optional[str]:
    """
    Scrapes the main textual content from a job description URL.

    This function attempts to fetch the HTML content of the given URL and parse it
    to extract the job description. It uses a series of heuristic selectors to identify
    the main content area by targeting common HTML tags and class names associated
    with job descriptions.

    Args:
        url (str): The URL of the job description page.

    Returns:
        Optional[str]: The extracted job description text as a single string,
                       or None if scraping fails or no substantial content is found.

    Important Operational Notes:
    - **Heuristic Nature**: This is a basic, heuristic-based scraper. Its success heavily depends
      on the HTML structure of the target website, which can vary significantly.
    - **Limitations**:
        - It may struggle with sites that heavily rely on JavaScript to render content dynamically
          if the core job description isn't present in the initial HTML fetched by `requests`.
        - Single Page Applications (SPAs) or sites with complex login/interaction requirements
          will likely not work.
        - Websites with strong anti-scraping measures might block requests or return captchas.
    - **Selector Robustness**: The list of `potential_containers` (selectors like `div` with class
      `job-description`) is based on common patterns but is not exhaustive and might become outdated
      as website designs change. It might fail on job sites with unique or frequently updated structures.
    - **Content Cleaning**: Basic cleaning (removing scripts, styles, etc.) is performed, but some
      irrelevant content might still be included.
    - **Alternatives**: For robust and production-level scraping, consider dedicated scraping
      frameworks (e.g., Scrapy, Playwright, Selenium) or professional web scraping services.
    - **Error Handling**: Basic error handling for network issues and HTTP errors is included, but
      unexpected site structures can lead to incomplete or incorrect extraction.
    """
    try:
        # Make an HTTP GET request to the URL, using defined headers and a timeout.
        response = requests.get(url, headers=DEFAULT_REQUEST_HEADERS, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4XX or 5XX)

        # Parse the HTML content of the page.
        soup = BeautifulSoup(response.content, 'html.parser')

        # Attempt to remove common irrelevant parts of the page (scripts, styles, nav, footer, etc.)
        # This helps to isolate the main content.
        for tag_name in ['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'iframe']:
            for tag in soup.find_all(tag_name):
                tag.decompose() # Removes the tag and its content from the parse tree.

        # Define a list of potential selectors for the main job description content.
        # These are tried in order. More specific selectors are usually better.
        potential_containers = [
            soup.find('div', class_=re.compile(r"job-description|jobdescription|description|content|jobDetails|jobdetails", re.I)),
            soup.find('article', class_=re.compile(r"job-description|jobdescription|content", re.I)),
            soup.find(id=re.compile(r"jobDescription|jobdescription|content", re.I)),
            soup.find('div', role='main'), # Added common role attribute
            soup.find('main'),             # HTML5 main content tag
            soup.body                      # Last resort: the entire body text
        ]

        text_content = ""
        # Iterate through potential containers and take the first one that yields substantial text.
        for container in potential_containers:
            if container:
                # Extract text, using newline as separator and stripping whitespace from lines.
                current_text = container.get_text(separator='\n', strip=True)
                # Prioritize longer text, assuming it's more likely the JD.
                if len(current_text) > len(text_content):
                    text_content = current_text
                
                # If a very long piece of text is found, assume it's the main content and break.
                if len(text_content) > 1000: # Increased threshold for more confidence
                    break
        
        # Return the cleaned text if it's not empty, otherwise None.
        return text_content.strip() if text_content and text_content.strip() else None

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (DNS failure, connection timeout, etc.).
        print(f"Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        # Handle other potential errors during scraping (e.g., parsing errors).
        print(f"Error scraping job description from {url}: {e}")
        return None

# --- Text Processing & Keyword Extraction ---
def extract_keywords_from_text(text: str, min_keyword_length: int = 3, top_n: int = 50) -> List[str]:
    """
    Extracts potential keywords from a given block of text.

    This function performs a simple frequency-based keyword extraction. It tokenizes
    the text into words, converts them to lowercase, removes common stop words and
    short words, and then returns the most frequent remaining words.

    Args:
        text (str): The text to extract keywords from.
        min_keyword_length (int): The minimum length for a word to be considered a keyword.
        top_n (int): The maximum number of most frequent keywords to return.

    Returns:
        List[str]: A list of extracted keywords, sorted by frequency in descending order.

    Important Notes:
    - This is a heuristic method and not a sophisticated Natural Language Processing (NLP)
      keyword extraction technique (like TF-IDF, RAKE, YAKE, or model-based approaches).
    - **Frequency-Based**: Its core logic relies on word frequency, which may not always
      correlate with actual importance or relevance in the context of skills or job requirements.
    - **Single Word Focus**: It primarily extracts single words. Multi-word keywords (e.g.,
      "machine learning", "data analysis") are not identified as single units unless they are
      hyphenated or concatenated in the text (e.g., "machine-learning").
    - **Stop Word List**: The effectiveness of filtering depends on the `stop_words` list. While
      expanded, it might still need domain-specific additions for optimal results in certain contexts.
    - **Context Agnostic**: The extraction does not consider the semantic context of words.
    """
    if not text:
        return []

    # Use regex to find words: sequences of alphanumeric characters, allowing hyphens and dots within words.
    # Convert text to lowercase to ensure case-insensitive keyword matching.
    words = re.findall(r'\b[a-zA-Z0-9.-]+\b', text.lower()) # Tokenize and normalize case

    # Expanded list of common English stop words to filter out noise.
    # This list is conservative; for specific domains, it might need further extension.
    stop_words = set([
        'and', 'the', 'is', 'in', 'it', 'to', 'a', 'of', 'for', 'on', 'with', 'as', 'at', 'by', 'an', 'or', 'if',
        'are', 'has', 'had', 'was', 'were', 'will', 'be', 'this', 'that', 'my', 'your', 'our', 'we', 'us', 'me',
        'he', 'she', 'they', 'them', 'just', 'so', 'than', 'then', 'not', 'all', 'any', 'some', 'such', 'no', 'nor',
        'can', 'do', 'get', 'go', 'up', 'out', 'about', 'who', 'what', 'when', 'where', 'why', 'how',
        'job', 'role', 'company', 'experience', 'skill', 'skills', 'work', 'team', 'position', 'candidate',
        'description', 'responsibilities', 'requirements', 'preferred', 'qualification', 'qualifications',
        'etc', 'e.g', 'i.e', 'br', 'p', 'li', 'div', 'span', 'ul', 'ol', 'strong', 'em' # Common HTML/formatting words
    ])
    
    # Filter words: must meet min_keyword_length and not be in stop_words.
    keywords = [word for word in words if len(word) >= min_keyword_length and word not in stop_words]

    # Count the frequency of each keyword.
    keyword_counts = Counter(keywords)

    # Return the `top_n` most common keywords.
    return [kw for kw, count in keyword_counts.most_common(top_n)]

# --- Comparison Logic ---
def compare_resume_to_job_description(
    parsed_resume_data: Dict[str, Any],
    job_description_text: str
) -> Dict[str, Any]:
    """
    Compares skills from parsed resume data with keywords extracted from a job description.

    This function identifies skills present in the resume that match keywords in the job
    description. It also suggests potential skills from the job description that might
    be missing from the resume. A heuristic match score is calculated based on the overlap.

    Args:
        parsed_resume_data (Dict[str, Any]): A dictionary containing parsed resume information,
                                             expected to have a "skills" key with a list of skills.
        job_description_text (str): The text of the job description.

    Returns:
        Dict[str, Any]: A dictionary containing the comparison results:
            - "matching_skills" (List[str]): Skills from the resume that are found (or are substrings of)
                                             keywords in the job description. Original casing from resume is preserved.
            - "missing_skills_from_jd" (List[str]): Keywords from the job description that are not found
                                                    in the resume's skills. These are suggestions and may
                                                    not all be actual skills.
            - "job_summary_keywords" (List[str]): A sample of the most common keywords extracted from the
                                                  job description (up to 20).
            - "match_score_heuristic" (float): A naive percentage score representing the overlap between
                                               resume skills and job description keywords. Ranges from 0.0 to 100.0.
    """
    comparison_results = {
        "matching_skills": [],
        "missing_skills_from_jd": [],
        "job_summary_keywords": [],
        "match_score_heuristic": 0.0 # Initialize a basic heuristic score
    }

    # Return empty results if essential inputs are missing.
    if not parsed_resume_data or not job_description_text:
        return comparison_results

    # Extract keywords from the job description text.
    jd_keywords_set = set(extract_keywords_from_text(job_description_text))
    # Store a sample of JD keywords in the results for context.
    comparison_results["job_summary_keywords"] = sorted(list(jd_keywords_set))[:20]

    # Get skills from the resume data; default to an empty list if not present or not a list.
    resume_skills = parsed_resume_data.get("skills", [])
    if not isinstance(resume_skills, list): resume_skills = []

    # Normalize resume skills to lowercase for case-insensitive comparison.
    # Filter out any None or empty skill entries.
    resume_skills_lower = set([str(skill).lower() for skill in resume_skills if skill and str(skill).strip()])

    # Find skills from the resume that match keywords in the job description.
    matching_skills_found = []
    for r_skill_lower in resume_skills_lower:
        # Check for direct match or if the resume skill is a substring of any JD keyword (e.g., "react" in "react.js").
        if r_skill_lower in jd_keywords_set or any(r_skill_lower in jd_kw for jd_kw in jd_keywords_set):
            # Try to find the original casing of the skill from the resume for display purposes.
            original_skill = next((s for s in resume_skills if str(s).lower() == r_skill_lower), r_skill_lower)
            matching_skills_found.append(original_skill)
    
    comparison_results["matching_skills"] = sorted(list(set(matching_skills_found)))

    # Identify potential skills mentioned in the JD that are not present in the resume.
    # This is heuristic: jd_keywords are raw frequent words and not necessarily all "skills".
    # It filters out JD keywords that are already matched (directly or as superstrings) by resume skills.
    missing_skills_suggestions = [
        jd_kw for jd_kw in jd_keywords_set  # Iterate through all unique keywords from the job description
        # Condition 1: The JD keyword is not directly present in the set of lowercase resume skills.
        if jd_kw not in resume_skills_lower and 
        # Condition 2: No resume skill is a substring of the current JD keyword.
        # This avoids suggesting "java" if "javascript" is in resume skills and "javascript" is the jd_kw.
        # However, it means if resume has "java" and JD has "javascript", "javascript" might still be suggested.
        # A more nuanced check might be needed if this behavior is not desired.
        not any(r_skill_lower in jd_kw for r_skill_lower in resume_skills_lower)
    ]
    # These are suggestions based on keyword matches and may not always represent actual required skills.
    # Their relevance should be critically evaluated by the user.
    comparison_results["missing_skills_from_jd"] = sorted(list(set(missing_skills_suggestions)))[:15] # Limit for brevity

    # Calculate a very naive heuristic match score.
    # Score = (Number of matching skills / Total unique terms (skills in resume + keywords in JD)) * 100
    # This score is basic and doesn't account for skill importance or context.
    if resume_skills_lower or jd_keywords_set: # Avoid division by zero if both are empty
        # Union of terms ensures each unique skill/keyword is counted once in the denominator.
        total_unique_terms = len(resume_skills_lower.union(jd_keywords_set))
        if total_unique_terms > 0:
            comparison_results["match_score_heuristic"] = round((len(comparison_results["matching_skills"]) / total_unique_terms) * 100, 2)
        else:
            # If total_unique_terms is 0, it means both resume_skills_lower and jd_keywords_set are empty.
            # If matching_skills is somehow not empty (shouldn't happen if others are empty), score 100, else 0.
            comparison_results["match_score_heuristic"] = 0.0 if not comparison_results["matching_skills"] else 100.0
    
    # Potential future enhancements:
    # - Weight skills based on where they appear in the JD (e.g., "Required Skills" vs. "Preferred").
    # - Analyze experience descriptions for contextual skill usage.
    # - Parse and compare years of experience.
    # - Match education levels and fields of study.

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
