from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
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
    return {"message": "AI Service is running", "version": "feature-job-search-v1"}

@app.post("/process-resume")
def process_resume(request: ResumeRequest):
    """
    Receives a file path (from Node.js), extracts text, 
    and returns structured data using LLM.
    """
    file_path = request.file_path
    temp_file = None
    
    try:
        # Check if file_path is a URL
        if file_path.startswith(('http://', 'https://')):
            import requests
            import tempfile
            
            # Download file
            response = requests.get(file_path)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to download file from URL")
            
            # Create temp file
            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf") # Assuming PDF for now, or detect from URL
            with os.fdopen(temp_fd, 'wb') as tmp:
                tmp.write(response.content)
            
            file_path = temp_path
            temp_file = temp_path
        
        # Check if file exists (local or downloaded temp)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found at {file_path}")
            
        # Extract Text
        text = extract_text_from_pdf(file_path)
        
        if not text:
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF")
        
        # Analyze with LLM
        analysis = analyze_resume_text(text)
            
        return {
            "success": True, 
            "text_preview": text[:200],
            "data": analysis
        }
        
    finally:
        # Cleanup temp file if it was created
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

# --- New Phase 4 Endpoints ---

from app.services.matcher import calculate_match_score
from app.services.scraper import scrape_job_description

class JobMatchRequest(BaseModel):
    resume_text: str
    job_description: str

class JobScrapeRequest(BaseModel):
    url: str

@app.post("/match-jobs")
def match_jobs(request: JobMatchRequest):
    """
    Compares resume text with job description and returns scoring.
    """
    result = calculate_match_score(request.resume_text, request.job_description)
    return {"success": True, "data": result}

@app.post("/scrape-job")
def scrape_job(request: JobScrapeRequest):
    """
    Scrapes job content from a URL.
    """
    content = scrape_job_description(request.url)
    if not content:
         raise HTTPException(status_code=400, detail="Failed to scrape content")
    return {"success": True, "data": content}

# --- Phase 5: External Job Recommendations ---
from app.services.llm import extract_search_criteria
from app.services.scraper import search_external_jobs

class RecommendJobsRequest(BaseModel):
    resume_text: str

@app.post("/recommend-jobs")
def recommend_jobs(request: RecommendJobsRequest):
    """
    1. Analyzes resume to find search criteria (role, level, skills).
    2. Searches Google for relevant jobs.
    3. Returns list of links.
    """
    # 1. Extract Criteria
    # 1. Extract Criteria
    criteria = extract_search_criteria(request.resume_text)
    
    if "error" in criteria:
        # Pass the error details to the client
        raise HTTPException(status_code=500, detail=criteria["error"])
    
    if not criteria or "query" not in criteria:
        # Fallback if LLM fails silently or returns formatting garbage
        query = "Software Engineer jobs"
    else:
        query = criteria["query"]
        
    # 2. Search Google
    jobs = search_external_jobs(query, limit=10)
    
    return {
        "success": True,
        "criteria": criteria,
        "data": jobs
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
