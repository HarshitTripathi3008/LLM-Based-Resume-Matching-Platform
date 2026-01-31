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

from googlesearch import search
import time

def search_external_jobs(query: str, limit: int = 5) -> list:
    """
    Searches Google for job postings matching the query.
    Returns a list of job objects.
    """
    results = []
    try:
        # Perform Google Search
        # advanced=True returns SearchResult objects with title, description, url
        search_results = search(query, num_results=limit, advanced=True)
        
        for res in search_results:
            results.append({
                "id": str(hash(res.url)),
                "title": res.title,
                "company": "External Source", # Hard to parse from Google title reliably without NLP
                "description": res.description,
                "url": res.url,
                "source": "Google Search"
            })
            
    except Exception as e:
        print(f"Google Search Error: {e}")
        # Fallback to mock data if quota exceeded or error
        return [
            {
                "id": "err_1",
                "title": "Error fetching real jobs",
                "company": "System",
                "description": "Please try again later. Google Search limit may have been reached.",
                "url": "#"
            }
        ]
        
    return results
