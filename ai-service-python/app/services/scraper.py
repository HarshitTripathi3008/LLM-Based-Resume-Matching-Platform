import requests
from bs4 import BeautifulSoup

def scrape_job_description(url: str) -> str:
    """
    Scrapes job description text from a given URL.
    Uses basic requests/bs4 for simplicity. 
    For complex SPAs (LinkedIn/Indeed), Playwright would be needed.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find common job description containers
        # This is a heuristic and varies by site
        content = ""
        
        # Priority to generic semantic tags
        main_content = soup.find('main') or soup.find('article') or soup.body
        
        if main_content:
            # Remove scripts and styles
            for script in main_content(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            content = main_content.get_text(separator="\n")
            
        return content.strip()[:10000] # Limit length

    except Exception as e:
        print(f"Scraping Error: {e}")
        return ""

def mock_scrape_job_portal(role: str) -> list:
    """
    Mock function to simulate searching for jobs on a portal.
    In production, this would use Playwright to search LinkedIn/Indeed.
    """
    # Mock Data for demonstration
    return [
        {
            "id": "job_101",
            "title": f"Senior {role} Developer",
            "company": "Tech Corp",
            "description": f"We are looking for a {role} expert with Node.js and Python experience...",
            "url": "https://example.com/job/101"
        },
        {
            "id": "job_102",
            "title": f"Junior {role} Engineer",
            "company": "Startup Inc",
            "description": "Entry level role. Must know algorithms and data structures.",
            "url": "https://example.com/job/102"
        }
    ]
