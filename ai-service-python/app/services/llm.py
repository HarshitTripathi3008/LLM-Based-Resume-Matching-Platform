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
        4. "experience": list of objects with "title", "company", "years" (number, approx), "description"
        5. "education": list of objects with "degree", "school", "year"
        6. "summary": a brief professional summary (2-3 sentences)
        7. "years_of_experience": total years of experience (number)

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
    Returns: { "experience_level": str, "domain": str, "top_skills": list, "query": str }
    """
    if not GROQ_API_KEY and not GEMINI_API_KEY:
        return {"error": "No API keys configured"}

    try:
        prompt = f"""
        You are a job search assistant. Analyze the resume text below and extract:
        1. "experience_level": "Junior", "Mid-Level", "Senior", "Lead", or "Intern" (based on years of exp).
        2. "domain": The primary role domain (e.g., "Frontend Developer", "Data Scientist", "DevOps Engineer").
        3. "degree": Highest degree (e.g., "Bachelors", "Masters", "PhD", or null).
        4. "top_skills": List of 3-5 most critical technical skills for their role.
        5. "query": A precise Google Search query to find specific job listings for this candidate.
           Example query: "Junior React Developer jobs in India" or "Senior Data Scientist remote jobs".
        
        RESUME TEXT:
        {text[:5000]}
        
        Return ONLY valid JSON.
        """
        
        response_text = call_llm(prompt, model_preference="groq")
        response_text = clean_json_response(response_text)
        return json.loads(response_text)
        
    except Exception as e:
        print(f"LLM Search Criteria Error: {e}")
        return {"error": f"LLM Failed: {str(e)}"}
