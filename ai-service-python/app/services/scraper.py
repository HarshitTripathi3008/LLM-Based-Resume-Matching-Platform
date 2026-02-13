import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

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

def search_google_jobs(query: str, limit: int = 10) -> list:
    """
    Searches Google Jobs via SerpApi (Best for India - Naukri, LinkedIn, etc.)
    """
    results = []
    api_key = os.getenv("SERPAPI_KEY")
    
    if not api_key:
        return []

    try:
        params = {
            "engine": "google_jobs",
            "q": query,
            "hl": "en",
            "gl": "in", # Target India
            "api_key": api_key,
            "num": limit
        }
        
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        data = response.json()
        
        if "jobs_results" in data:
            for job in data["jobs_results"]:
                results.append({
                    "id": job.get("job_id", ""),
                    "title": job.get("title", ""),
                    "company": job.get("company_name", "Unknown"),
                    "description": job.get("description", "")[:200] + "...",
                    "url": job.get("share_link", "#") or job.get("related_links", [{}])[0].get("link", "#"),
                    "source": "Google Jobs (" + job.get("via", "Unknown") + ")", # e.g. "via Naukri"
                    "location": job.get("location", "")
                })
    except Exception as e:
        print(f"SerpApi Error: {e}")
        
    return results

def search_external_jobs(query: str, limit: int = 10) -> list:
    """
    Searches for jobs using multiple free job board APIs.
    No rate limits, completely free.
    """
    results = []
    
    try:
        # Option 0: Google Jobs (Best for India)
        google_limit = limit  # Give full limit to Google first
        google_results = search_google_jobs(query, limit=google_limit)
        results.extend(google_results)
        
        # If we have enough results, we can stop or fetch fewer from others
        remaining_limit = limit - len(results)
        if remaining_limit <= 0:
            return results

        # Option 1: Adzuna API (Free tier: 1000 calls/month)
        # Sign up at: https://developer.adzuna.com/
        adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        adzuna_api_key = os.getenv("ADZUNA_API_KEY")
        
        if adzuna_app_id and adzuna_api_key:
            try:
                url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
                params = {
                    "app_id": adzuna_app_id,
                    "app_key": adzuna_api_key,
                    "results_per_page": remaining_limit,
                    "what": query,
                    "content-type": "application/json"
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for job in data.get("results", []):
                        results.append({
                            "id": job.get("id", ""),
                            "title": job.get("title", ""),
                            "company": job.get("company", {}).get("display_name", "Unknown"),
                            "description": job.get("description", "")[:200] + "...",
                            "url": job.get("redirect_url", "#"),
                            "source": "Adzuna"
                        })
                    
                    if len(results) >= limit:
                        return results
            except Exception as e:
                print(f"Adzuna API Error: {e}")
        
        # Option 2: The Muse API (Free, no key required)
        remaining_limit = limit - len(results)
        if remaining_limit > 0:
            try:
                url = "https://www.themuse.com/api/public/jobs"
                params = {
                    "page": 0,
                    "descending": True,
                    "api_key": "public",
                    "category": query.split()[0] if query else "Software Engineer"
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for job in data.get("results", [])[:remaining_limit]:
                        results.append({
                            "id": str(job.get("id", "")),
                            "title": job.get("name", ""),
                            "company": job.get("company", {}).get("name", "Unknown"),
                            "description": (job.get("contents", "") or "No description")[:200] + "...",
                            "url": job.get("refs", {}).get("landing_page", "#"),
                            "source": "The Muse"
                        })
            except Exception as e:
                print(f"The Muse API Error: {e}")
        
        # Option 3: Remotive API (Free, remote jobs)
        remaining_limit = limit - len(results)
        if remaining_limit > 0:
            try:
                url = "https://remotive.com/api/remote-jobs"
                params = {
                    "search": query,
                    "limit": remaining_limit
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for job in data.get("jobs", [])[:remaining_limit]:
                        results.append({
                            "id": str(job.get("id", "")),
                            "title": job.get("title", ""),
                            "company": job.get("company_name", "Unknown"),
                            "description": job.get("description", "")[:200] + "...",
                            "url": job.get("url", "#"),
                            "source": "Remotive"
                        })
            except Exception as e:
                print(f"Remotive API Error: {e}")
            
    except Exception as e:
        print(f"Job Search Error: {e}")
    
    # Fallback: Return helpful message if all APIs fail
    if not results:
        return [
            {
                "id": "setup_1",
                "title": "No Jobs Found / Setup Required",
                "company": "System",
                "description": "Please ensure SERPAPI_KEY or ADZUNA_APP_ID is set in .env to fetch jobs.",
                "url": "https://serpapi.com/",
                "source": "System Message"
            }
        ]
        
    return results
