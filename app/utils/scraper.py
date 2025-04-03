import requests
from bs4 import BeautifulSoup

def get_page_text(url):
    # Mimic a regular browser request with headers
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/103.0.0.0 Safari/537.36'
        )
    }
    
    # Fetch the page content
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return None
    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract text from the HTML, using a newline as a separator for clarity
    page_text = soup.get_text(separator='\n', strip=True)
    
    return page_text

if __name__ == "__main__":
    # Replace this URL with the actual job posting URL you want to scrape
    url = "https://jobs.lever.co/nominal/e0922dce-30a1-41cf-bee3-80833a714cbd"
    text = get_page_text(url)
    
    if text:
        print(text)
