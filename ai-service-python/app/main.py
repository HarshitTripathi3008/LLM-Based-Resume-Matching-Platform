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
    return {"message": "AI Service is running"}

@app.post("/process-resume")
def process_resume(request: ResumeRequest):
    """
    Receives a file path (from Node.js), extracts text, 
    and returns structured data using LLM.
    """
    file_path = request.file_path
    
    # Check if file exists
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

# --- New Phase 4 Endpoints ---

from app.services.matcher import calculate_match_score
from app.services.scraper import scrape_job_description, mock_scrape_job_portal

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


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
