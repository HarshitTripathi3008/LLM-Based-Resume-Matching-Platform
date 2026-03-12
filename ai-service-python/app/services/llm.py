import google.generativeai as genai
from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configure API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def call_llm(prompt: str, model_preference: str = "groq") -> str:
    """
    Calls LLM with automatic fallback.
    Primary: Groq (fast, free)
    Fallback: Gemini (reliable)
    """
    
    # Try Groq first
    if groq_client and model_preference == "groq":
        try:
            response = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert HR AI assistant. Always return valid JSON without markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",  # Fast and accurate
                temperature=0.3,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq failed: {e}. Falling back to Gemini...")
    
    # Fallback to Gemini
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Both Groq and Gemini failed. Groq: {e}")
    
    raise Exception("No valid API keys configured")

def clean_json_response(text: str) -> str:
    """Remove markdown formatting from LLM response"""
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def analyze_resume_text(text: str) -> dict:
    """
    Analyzes resume text using Groq (primary) or Gemini (fallback).
    """
    if not GROQ_API_KEY and not GEMINI_API_KEY:
        return {"error": "No API keys configured"}

    try:
        prompt = f"""
        You are an expert HR AI. Extract structured data from the following resume text.
        Return ONLY valid JSON. Do not include markdown formatting like ```json ... ```.
        
        Fields to extract:
        1. "name": candidate name
        2. "email": candidate email
        3. "skills": list of technical and soft skills (strings)
        4. "experience": list of objects with "title", "company", "years" (number), "description". 
           IMPORTANT: Only include PROFESSIONAL work (jobs, internships). Do NOT include personal or academic projects here.
        5. "projects": list of objects with "title", "technologies", "description". 
           IMPORTANT: Put all personal, academic, or group projects here. Do NOT include a "years" field for projects.
        6. "education": list of objects with "degree", "school", "year"
        7. "summary": a brief professional summary (2-3 sentences)
        8. "years_of_experience": total years of professional work experience ONLY (number). 
           CRITICAL: Do NOT include time spent on projects or education in this total.

        RESUME TEXT:
        {text[:10000]} 
        """

        response_text = call_llm(prompt, model_preference="groq")
        response_text = clean_json_response(response_text)
        return json.loads(response_text)

    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": f"Failed to analyze resume: {str(e)}"}

def extract_search_criteria(text: str) -> dict:
    """
    Extracts criteria for searching external jobs.
    Returns: { "experience_level": str, "domain": str, "years_of_experience": int, "top_skills": list, "query": str }
    """
    if not GROQ_API_KEY and not GEMINI_API_KEY:
        return {"error": "No API keys configured"}

    try:
        prompt = f"""
You are a job search specialist. Analyze the resume below and extract structured job search data.

STEP 1 — Count total years of PROFESSIONAL work experience (jobs, internships). 
         CRITICAL: Do NOT count personal projects, academic projects, or time spent in education.
         A candidate with multiple projects but no actual job history should have 0 years of experience.

STEP 2 — Map years_of_experience to experience_level using ONLY these strict rules:
  0–1 years → "Intern"
  1–3 years → "Junior"
  3–6 years → "Mid-Level"
  6–10 years → "Senior"
  10+ years  → "Lead"

STEP 3 — Identify the primary job domain (e.g., "Frontend Developer", "Data Scientist", "Backend Engineer", "Full Stack Developer").

STEP 4 — Extract the 3–5 most relevant technical skills for their domain.

STEP 5 — Build a concise, experience-appropriate Google Search query for jobs in INDIA.
  - The query MUST include the experience_level prefix (e.g., "Junior", "Mid-Level").
  - Keep the query SHORT and precise (no more than 7 words).
  - Target India specifically (e.g., "in India" or "Bangalore" or "Remote India").
  - DO NOT include skills that over-qualify the candidate.
  - Example for 2 years experience: "Junior React Developer jobs in India"
  - Example for 4 years: "Mid-Level Full Stack Developer Bangalore"

RESUME TEXT:
{text[:6000]}

Return ONLY valid JSON in this exact format:
{{
  "years_of_experience": <integer>,
  "experience_level": "Junior",
  "domain": "Frontend Developer",
  "top_skills": ["React", "JavaScript", "CSS"],
  "query": "Junior Frontend Developer jobs in India"
}}
"""
        
        response_text = call_llm(prompt, model_preference="groq")
        response_text = clean_json_response(response_text)
        if not response_text or response_text.strip() == "":
            raise ValueError("LLM returned an empty response. Check API keys and quota.")
        return json.loads(response_text)
        
    except Exception as e:
        print(f"LLM Search Criteria Error: {e}")
        return {"error": f"LLM Failed: {str(e)}"}
