import requests
from bs4 import BeautifulSoup, Comment # Import Comment to remove comments
import re
from typing import List, Dict, Optional, Any # For type hinting


# --- Constants and Pre-compiled Regex ---
SHARE_APPLY_PATTERN = re.compile(r'\b(share this job|apply now|report this job)\b', re.IGNORECASE)
MULTIPLE_NEWLINES_PATTERN = re.compile(r'\n\s*\n+') # Matches 2 or more newlines with optional space between

# Common selectors for job descriptions, ordered by likely relevance/specificity
POTENTIAL_SELECTORS: List[Dict[str, Any]] = [
    {'class_': re.compile(r'job-description|job_description|jobDescription|jobdescript(ion)?|posting-content|job-details-content|jobad')},
    {'class_': re.compile(r'job-details|job_details|jobDetails|jobdetail|job-listing-details|job-summary')},
    {'id': re.compile(r'job-description|job_description|jobDescription|job-details|jobad')},
    {'tag': 'article'}, # Often contains main content
    {'tag': 'main'},    # HTML5 main content tag
    {'tag': 'div', 'class_': re.compile(r'content|main-content|job-content|description|jobAdDetails|jobSummary|jobbody')},
    # Example for specific job boards (commented out, as these change often and need maintenance)
    # {'class_': 'jobsearch-JobComponent-description'}, # Example for Indeed
    # {'class_': 'description__text'},                # Example for LinkedIn (often JS-rendered)
]

# Keywords to help identify relevant content sections
JOB_KEYWORDS: List[str] = [
    'responsibilities', 'qualifications', 'duties', 'experience', 'requirements',
    'skills', 'benefits', 'salary', 'about the role', 'job summary', 'position summary'
]


def _clean_text(text: str) -> str:
    """Helper function to perform basic text cleaning on extracted content."""
    if not text:
        return ""
    # Remove common social sharing/apply button text that might be caught
    text = SHARE_APPLY_PATTERN.sub('', text)
    # Consolidate multiple newlines into a maximum of two (like paragraphs)
    text = MULTIPLE_NEWLINES_PATTERN.sub('\n\n', text)
    return text.strip()

def scrape_job_posting(url: str) -> str:
    """
    Fetches content from a URL and extracts the main job description text using heuristics.

    Args:
        url: The URL of the job posting.

    Returns:
        The extracted and cleaned job description text as a string.
        If an error occurs or content cannot be reliably extracted, an error message string is returned.
    """
    if not (url.startswith('http://') or url.startswith('https://')):
        # Basic check to ensure a scheme is present, defaulting to https
        url = 'https://' + url

    try:
        headers = { # Standard browser-like headers
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'DNT': '1', # Do Not Track
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(url, headers=headers, timeout=15) # Increased timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

    except requests.exceptions.Timeout:
        return f"Error: Timeout after 15 seconds trying to fetch URL: {url}"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} while fetching URL: {url}"
    except requests.exceptions.ConnectionError:
        return f"Error: Connection failed for URL: {url}. Please check the network or hostname."
    except requests.exceptions.RequestException as e: # Catch-all for other requests library errors
        return f"Error: An issue occurred while trying to fetch the URL: {e}"

    try:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove common non-content tags to clean up the HTML structure first
        for unwanted_tag_name in ['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'noscript', 'link', 'meta']:
            for tag in soup.find_all(unwanted_tag_name):
                tag.decompose()
        # Remove HTML comments
        for comment in soup.find_all(string=lambda text_content: isinstance(text_content, Comment)):
            comment.extract()

    except Exception as e:
        return f"Error: Failed during initial HTML parsing: {e}"

    extracted_text = ""
    # Attempt extraction using predefined selectors
    for selector_method in POTENTIAL_SELECTORS:
        try:
            elements: List[Any] = [] # Ensure elements is always a list
            if 'tag' in selector_method and 'class_' not in selector_method and 'id' not in selector_method:
                elements = soup.find_all(selector_method['tag'])
            elif 'class_' in selector_method: # Allows searching by class, optionally with a tag
                elements = soup.find_all(selector_method.get('tag', True), class_=selector_method['class_'])
            elif 'id' in selector_method: # Allows searching by id, optionally with a tag
                elements = soup.find_all(selector_method.get('tag', True), id=selector_method['id'])
            else:
                continue # Skip if selector definition is incomplete
        except Exception as e:
            print(f"Scraper Warning: Malformed selector {selector_method} resulted in error: {e}")
            continue

        if elements:
            best_element_text = ""
            max_relevance_score = 0 # Using a simple score instead of just max_len

            for element in elements:
                current_text = element.get_text(separator='\n', strip=True)
                len_current_text = len(current_text)

                # Conditions for relevance
                is_long_enough = len_current_text > 200 # Avoid tiny, irrelevant divs
                # Avoid capturing the entire page body if it's mistakenly selected by a broad selector
                soup_text_len = len(soup.get_text()) if soup.get_text() else float('inf')
                is_not_too_long = len_current_text < (0.9 * soup_text_len)

                if is_long_enough and is_not_too_long:
                    keyword_hits = sum(1 for keyword in JOB_KEYWORDS if keyword in current_text.lower())
                    # Simple relevance: length weighted by keyword presence
                    current_relevance_score = len_current_text * (1 + keyword_hits * 0.5)

                    if current_relevance_score > max_relevance_score:
                        max_relevance_score = current_relevance_score
                        best_element_text = current_text

            if best_element_text:
                extracted_text = best_element_text
                break # Found a good candidate from primary selectors

    # Fallback if no specific selectors yielded good results
    if not extracted_text:
        if soup.body:
            body_text = soup.body.get_text(separator='\n', strip=True)
            if len(body_text) > 5000: # If body text is very long, try to find meaningful blocks
                meaningful_blocks = []
                for para_text in body_text.split('\n\n'): # Split by paragraphs
                    if len(para_text) > 150 and any(keyword in para_text.lower() for keyword in JOB_KEYWORDS):
                        meaningful_blocks.append(para_text)
                if meaningful_blocks:
                    extracted_text = "\n\n".join(meaningful_blocks)
                else: # If still no specific blocks, take a sizable chunk of the body
                    extracted_text = body_text[:4000] + "..." # Truncate very long fallbacks
            elif body_text: # Body text is not excessively long
                 extracted_text = body_text
            else:
                 return "Error: Could not extract job description. No content found in HTML body."
        else:
            return "Error: Could not extract job description. HTML structure might be unusual or body tag is missing."

    cleaned_text = _clean_text(extracted_text)
    if not cleaned_text or len(cleaned_text) < 100 : # Final check on content length
        return "Error: Could not extract sufficient job description content. The content found was too short after cleaning. Try pasting the text directly."

    return cleaned_text

# --- Test Section (for direct execution) ---
if __name__ == '__main__':
    # Provide test URLs here when running this script directly
    test_urls_for_scraper = [
        # e.g., "https://www.somejobboard.com/path/to/job"
    ]

    if not test_urls_for_scraper:
        print("No test URLs provided in __main__ block for scraper.py. Direct testing skipped.")

    for i, url_to_test in enumerate(test_urls_for_scraper):
        print(f"\n--- Testing URL {i+1}: {url_to_test} ---")
        result = scrape_job_posting(url_to_test)
        print(f"Result (first 500 chars):\n{result[:500]}{'...' if len(result) > 500 else ''}")

    print("\n--- Testing with a known non-existent URL ---")
    result_bad = scrape_job_posting("http://thishostshouldnotexist12345.com/job")
    print(result_bad)

    print("\n--- Testing with a URL missing http scheme ---")
    result_non_http = scrape_job_posting("example.com/fakepath") # Will prepend https://
    print(result_non_http)
    pass
