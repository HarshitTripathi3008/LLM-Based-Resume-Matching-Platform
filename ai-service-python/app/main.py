from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.parser import extract_text_from_pdf
from app.services.llm import analyze_resume_text

app = FastAPI(title="AI Resume Service")


class ResumeRequest(BaseModel):
    file_path: str


@app.get("/")
def read_root():
    return {"message": "AI Service is running", "version": "feature-job-search-v2"}


@app.post("/process-resume")
def process_resume(request: ResumeRequest):
    """
    Receives a file path (from Node.js), extracts text,
    and returns structured data using LLM.
    """
    file_path = request.file_path
    temp_file = None

    try:
        if file_path.startswith(('http://', 'https://')):
            import requests
            import tempfile

            response = requests.get(file_path)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to download file from URL")

            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(temp_fd, 'wb') as tmp:
                tmp.write(response.content)

            file_path = temp_path
            temp_file = temp_path

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found at {file_path}")

        text = extract_text_from_pdf(file_path)

        if not text:
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF")

        analysis = analyze_resume_text(text)

        return {
            "success": True,
            "text_preview": text[:200],
            "data": analysis
        }

    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


# --- Phase 4 Endpoints ---

from app.services.matcher import calculate_match_score
from app.services.scraper import scrape_job_description


class JobMatchRequest(BaseModel):
    resume_text: str
    job_description: str


class JobScrapeRequest(BaseModel):
    url: str


@app.post("/match-jobs")
def match_jobs(request: JobMatchRequest):
    """Compares resume text with job description and returns scoring."""
    result = calculate_match_score(request.resume_text, request.job_description)
    return {"success": True, "data": result}


@app.post("/scrape-job")
def scrape_job(request: JobScrapeRequest):
    """Scrapes job content from a URL."""
    content = scrape_job_description(request.url)
    if not content:
        raise HTTPException(status_code=400, detail="Failed to scrape content")
    return {"success": True, "data": content}


# --- Phase 5: External Job Recommendations ---

from app.services.llm import extract_search_criteria
from app.services.scraper import search_external_jobs


class RecommendJobsRequest(BaseModel):
    resume_text: str
    parsed_data: Optional[dict] = None  # Pre-parsed structured data from Node.js


def _years_to_level(years: float) -> str:
    """Map total years of experience to a job level label."""
    if years < 1:
        return "Intern"
    elif years < 3:
        return "Junior"
    elif years < 6:
        return "Mid-Level"
    elif years < 10:
        return "Senior"
    else:
        return "Lead"


# Keyword maps for domain inference from job titles and skills
_DOMAIN_KEYWORDS = [
    (["backend", "node", "express", "fastapi", "django", "spring", "api", "server", "microservice"], "Backend Developer"),
    (["frontend", "react", "angular", "vue", "next", "nuxt", "ui", "css", "html", "tailwind"],       "Frontend Developer"),
    (["full stack", "fullstack", "mern", "mean", "full-stack"],                                       "Full Stack Developer"),
    (["data science", "machine learning", "ml", "deep learning", "pytorch", "tensorflow", "nlp"],    "Data Scientist"),
    (["devops", "kubernetes", "docker", "ci/cd", "jenkins", "terraform", "ansible", "aws", "cloud"], "DevOps Engineer"),
    (["android", "ios", "flutter", "react native", "swift", "kotlin", "mobile"],                     "Mobile Developer"),
    (["blockchain", "solidity", "web3", "smart contract"],                                            "Blockchain Developer"),
]


def _infer_domain(titles: list, skills: list) -> str:
    """
    Infer job domain from experience titles and skills.
    Uses a keyword-matching priority list so backend skills
    are never misclassified as frontend.
    """
    combined = " ".join(titles + skills).lower()
    for keywords, domain in _DOMAIN_KEYWORDS:
        if any(kw in combined for kw in keywords):
            return domain
    return "Software Developer"


@app.post("/recommend-jobs")
def recommend_jobs(request: RecommendJobsRequest):
    """
    1. Build search criteria from parsedData (fast path) or via LLM (slow path).
    2. Search for experience-appropriate jobs via SerpApi / external APIs.
    3. Return job list.
    """
    criteria = {}

    # --- Fast path: use pre-parsed structured data from Node.js ---
    if request.parsed_data and isinstance(request.parsed_data, dict):
        p = request.parsed_data

        experience_entries = p.get("experience", [])
        total_years = sum(float(e.get("years", 0)) for e in experience_entries)
        # Use explicit field if the LLM already calculated it during onboarding
        total_years = float(p.get("years_of_experience", total_years))

        skills = p.get("skills", [])
        titles = [e.get("title", "") for e in experience_entries]

        domain = _infer_domain(titles, skills)
        level = _years_to_level(total_years)
        top_skills = skills[:5]

        criteria = {
            "years_of_experience": round(total_years, 1),
            "experience_level": level,
            "domain": domain,
            "top_skills": top_skills,
        }

    else:
        # --- Slow path: extract criteria from resume text via LLM ---
        # Try LLM; if it fails, fall back to keyword matching on the raw text
        try:
            llm_result = extract_search_criteria(request.resume_text)
            if "error" not in llm_result:
                criteria = llm_result
            else:
                raise ValueError(llm_result["error"])
        except Exception as e:
            print(f"LLM slow path failed: {e}. Using keyword fallback.")
            # Keyword-based fallback: scan the resume text directly
            text_lower = request.resume_text.lower()
            words = text_lower.split()
            domain = _infer_domain([], words)
            # Rough year count: assume 0 if no work history clues
            criteria = {
                "years_of_experience": 0,
                "experience_level": "Junior",
                "domain": domain,
                "top_skills": [],
            }

    # Build an experience-anchored, precise search query
    years = criteria.get("years_of_experience", 0)
    level = _years_to_level(float(years) if years else 0)
    domain = criteria.get("domain", "Software Developer")
    top_skills = criteria.get("top_skills", [])

    # Use the single most relevant skill as a qualifier
    skill_tag = top_skills[0] if top_skills else ""
    
    # Simpler query for better hit rate
    if skill_tag:
        # e.g. "Junior Node.js India" or "Intern React Bangalore"
        query = f"{level} {skill_tag} {domain} India"
    else:
        query = f"{level} {domain} India"

    jobs = search_external_jobs(query, limit=10)

    return {
        "success": True,
        "criteria": {**criteria, "resolved_level": level, "final_query": query},
        "data": jobs,
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
