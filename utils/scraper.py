import requests
from bs4 import BeautifulSoup, Comment # Import Comment to remove comments
import re

# Pre-compiled regex for cleaning
SHARE_APPLY_PATTERN = re.compile(r'\b(share this job|apply now|report this job)\b', re.IGNORECASE)
MULTIPLE_NEWLINES_PATTERN = re.compile(r'\n\s*\n+') # Matches 2 or more newlines with optional space between

# Common selectors for job descriptions (can be expanded)
# Order matters: more specific or common ones should be tried first.
POTENTIAL_SELECTORS = [
    {'class_': re.compile(r'job-description|job_description|jobDescription|jobdescript(ion)?|posting-content|job-details-content')},
    {'class_': re.compile(r'job-details|job_details|jobDetails|jobdetail|job-listing-details')},
    {'id': re.compile(r'job-description|job_description|jobDescription|job-details')},
    {'tag': 'article'},
    {'tag': 'main'},
    {'tag': 'div', 'class_': re.compile(r'content|main-content|job-content|description|jobAdDetails|jobSummary')},
    # Add more specific selectors for known job boards if necessary, e.g.:
    # {'class_': 'jobsearch-JobComponent-description'}, # Indeed (example, might change)
    # {'class_': 'description__text'}, # LinkedIn (example, might change, often JS rendered)
]

JOB_KEYWORDS = ['responsibilities', 'qualifications', 'duties', 'experience', 'requirements', 'skills', 'benefits', 'salary']


def _clean_text(text: str) -> str:
    """Helper function to perform basic text cleaning."""
    if not text:
        return ""
    text = SHARE_APPLY_PATTERN.sub('', text) # Remove "share this job", "apply now" etc.
    text = MULTIPLE_NEWLINES_PATTERN.sub('\n\n', text) # Consolidate multiple newlines to a double newline
    return text.strip()

def scrape_job_posting(url: str) -> str:
    """
    Fetches content from a URL and extracts the main job description text using heuristics.

    Args:
        url: The URL of the job posting.

    Returns:
        The extracted and cleaned job description text, or an error message string.
    """
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url # Add scheme if missing

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br', # Added to handle compressed content
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'DNT': '1', # Do Not Track
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(url, headers=headers, timeout=15) # Increased timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

    except requests.exceptions.Timeout:
        return f"Error fetching URL: Timeout after 15 seconds for {url}"
    except requests.exceptions.HTTPError as e:
        return f"Error fetching URL: HTTP Error {e.response.status_code} for {url}"
    except requests.exceptions.ConnectionError:
        return f"Error fetching URL: Connection error for {url}. Check network or hostname."
    except requests.exceptions.RequestException as e: # Catch-all for other requests errors
        return f"Error fetching URL: {e}"

    try:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script, style, nav, header, footer, and comment tags as they usually don't contain main content
        for unwanted_tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'noscript']):
            unwanted_tag.decompose()
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

    except Exception as e: # Catch errors during initial soup processing
        return f"Error parsing HTML content: {e}"


    extracted_text = ""
    # Try heuristic selectors
    for selector_method in POTENTIAL_SELECTORS:
        try:
            if 'tag' in selector_method and 'class_' not in selector_method and 'id' not in selector_method:
                elements = soup.find_all(selector_method['tag'])
            elif 'class_' in selector_method:
                elements = soup.find_all(selector_method.get('tag', True), class_=selector_method['class_'])
            elif 'id' in selector_method:
                elements = soup.find_all(selector_method.get('tag', True), id=selector_method['id'])
            else:
                continue # Invalid selector definition
        except Exception as e: # Catch errors if a selector is malformed (e.g. bad regex in re.compile)
            print(f"Scraper warning: Malformed selector {selector_method} - {e}")
            continue

        if elements:
            best_element_text = ""
            max_len = 0
            # Iterate through found elements to find the one with the most relevant text
            for element in elements:
                current_text = element.get_text(separator='\n', strip=True)
                # Heuristic: check length and presence of job-related keywords
                # The length check (not too short, not the entire page) helps filter noise.
                if 200 < len(current_text) < (0.9 * len(soup.get_text()) if soup.get_text() else float('inf')):
                    if any(keyword in current_text.lower() for keyword in JOB_KEYWORDS):
                        if len(current_text) > max_len:
                            max_len = len(current_text)
                            best_element_text = current_text

            if best_element_text:
                extracted_text = best_element_text
                break # Found a good candidate, stop searching

    if not extracted_text:
        # Fallback: get all text from body if specific selectors fail
        if soup.body:
            body_text = soup.body.get_text(separator='\n', strip=True)
            # Attempt a very basic content distillation if body_text is too long/noisy
            if len(body_text) > 5000: # Arbitrary threshold for "too noisy"
                meaningful_blocks = []
                for para_text in body_text.split('\n\n'): # Split by double newlines
                    if len(para_text) > 150 and any(keyword in para_text.lower() for keyword in JOB_KEYWORDS):
                        meaningful_blocks.append(para_text)
                if meaningful_blocks:
                    extracted_text = "\n\n".join(meaningful_blocks)
                else: # If no meaningful blocks, take first N chars of body, or just give up
                    extracted_text = body_text[:3000] + "..." # Truncate very long fallbacks
            elif body_text: # Body text is not excessively long
                 extracted_text = body_text
            else: # No body text found
                 return "Could not automatically extract the main job description. No content found in body."
        else:
            return "Could not automatically extract the main job description. HTML structure might be unusual or empty."

    cleaned_text = _clean_text(extracted_text)
    if not cleaned_text or len(cleaned_text) < 100 : # If after cleaning, text is too short
        return "Could not extract sufficient job description content. Try pasting the text directly."

    return cleaned_text

if __name__ == '__main__':
    test_urls = [
        # Replace with actual, currently accessible job posting URLs for real testing
        # "https://www.example.com/job1",
        # "https://www.anotherjobsite.com/postingXYZ"
    ]

    if not test_urls:
        print("No test URLs provided in __main__ block. Scraper testing skipped.")

    for i, url_to_test in enumerate(test_urls):
        print(f"\n--- Testing URL {i+1}: {url_to_test} ---")
        result = scrape_job_posting(url_to_test)
        print(f"Result (first 500 chars):\n{result[:500]}{'...' if len(result) > 500 else ''}")

    print("\n--- Testing with a known bad URL ---")
    result_bad = scrape_job_posting("http://thisurldoesnotexistandshouldfail123abc.com")
    print(result_bad)

    print("\n--- Testing with a non-HTTP URL ---")
    result_non_http = scrape_job_posting("notaurl")
    print(result_non_http)
    pass
