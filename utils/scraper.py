import requests
from bs4 import BeautifulSoup
import re

def scrape_job_posting(url: str) -> str:
    """
    Fetches content from a URL and extracts the main job description text.
    Uses heuristics to find the relevant content.
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url # Basic scheme check

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {e}"

    soup = BeautifulSoup(response.content, 'html.parser')

    # Heuristics to find the main job description content
    # These selectors are common but might need adjustment for specific sites.
    potential_selectors = [
        {'tag': 'article'},
        {'tag': 'main'},
        {'class_': re.compile(r'job-description|job_description|jobDescription|jobdescript')},
        {'class_': re.compile(r'job-details|job_details|jobDetails|jobdetail')},
        {'id': re.compile(r'job-description|job_description|jobDescription')},
        {'tag': 'div', 'class_': re.compile(r'content|main-content|job-content|description')},
        # Add more specific selectors if known for common job boards
        # e.g. for LinkedIn: {'class_': 'description__text'} (but this changes)
    ]

    extracted_text = ""
    for selector_method in potential_selectors:
        if 'tag' in selector_method and 'class_' not in selector_method and 'id' not in selector_method:
            elements = soup.find_all(selector_method['tag'])
        elif 'class_' in selector_method:
            elements = soup.find_all(selector_method.get('tag', True), class_=selector_method['class_'])
        elif 'id' in selector_method:
            elements = soup.find_all(selector_method.get('tag', True), id=selector_method['id'])
        else:
            elements = []

        if elements:
            # Prioritize elements with more text, but be wary of a parent containing too much (like whole page)
            best_element = None
            max_len = 0
            for element in elements:
                current_text = element.get_text(separator='\n', strip=True)
                if len(current_text) > max_len and len(current_text) < 0.8 * len(soup.get_text()): # Avoid capturing the whole page
                    # Check for common job description keywords to increase confidence
                    if any(kw in current_text.lower() for kw in ['responsibilities', 'qualifications', 'duties', 'experience', 'requirements']):
                        max_len = len(current_text)
                        best_element = element

            if best_element:
                extracted_text = best_element.get_text(separator='\n', strip=True)
                # Further clean up: remove "share" buttons, "apply" links if they are text noise
                extracted_text = re.sub(r'\b(share this job|apply now|report this job)\b', '', extracted_text, flags=re.IGNORECASE)
                extracted_text = re.sub(r'\n\s*\n', '\n', extracted_text) # Consolidate multiple newlines
                break # Stop after the first successful heuristic match that yields good content

    if not extracted_text:
        # Fallback: try to get all text from body, but this can be very noisy
        body_text = soup.body.get_text(separator='\n', strip=True) if soup.body else "Could not find body content."
        # Basic cleaning for fallback
        body_text = re.sub(r'\s*\n\s*', '\n', body_text) # Consolidate multiple newlines
        # Try to filter for a reasonable chunk of text - very heuristic
        # Look for a block of text that seems paragraph-like
        paragraphs = body_text.split('\n\n')
        longest_paragraph_block = ""
        current_max_len = 0
        for p_block in paragraphs:
            if len(p_block) > 300 and len(p_block) > current_max_len: # Arbitrary length check
                 if any(kw in p_block.lower() for kw in ['responsibilities', 'qualifications', 'duties', 'experience', 'requirements']):
                    current_max_len = len(p_block)
                    longest_paragraph_block = p_block

        if longest_paragraph_block:
            extracted_text = longest_paragraph_block
        else: # If still nothing good, return a message
            return "Could not automatically extract the main job description. The website structure might be too complex or unsupported. Try pasting the text directly."


    return extracted_text.strip()

if __name__ == '__main__':
    # Test URLs (these might become outdated or blocked)
    test_urls = [
        "https://www.linkedin.com/jobs/view/software-engineer-at-linkedin-1234567890", # Example, likely won't work directly due to JS/login
        "https://www.indeed.com/viewjob?jk=somejobkey", # Example
        "https://careers.google.com/jobs/results/some-id/", # Example
        "https://example.com/careers/job-posting-123" # A generic example
    ]

    # A more realistic test would be with a known, simple HTML structure saved locally or a live URL known to be accessible.
    # For now, this is a placeholder for testing.
    # print(f"Testing with a placeholder URL (will likely fail if not a real, accessible job posting): {test_urls[3]}")
    # result = scrape_job_posting(test_urls[3])
    # print("\n--- Scraped Text ---")
    # print(result[:1000] + "..." if result else "No text extracted.")

    # Test with a non-existent or problematic URL
    # print("\n--- Testing with a bad URL ---")
    # result_bad = scrape_job_posting("http://thisurldoesnotexistandshouldfail.com")
    # print(result_bad)

    # Test with a non-HTTP URL
    # print("\n--- Testing with a non-HTTP URL ---")
    # result_non_http = scrape_job_posting("notaurl")
    # print(result_non_http)
    pass
