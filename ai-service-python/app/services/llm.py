import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def analyze_resume_text(text: str) -> dict:
    """
    Analyzes resume text using Gemini LLM and returns structured JSON.
    """
    if not api_key or "PLACEHOLDER" in api_key:
        return {"error": "Gemini API Key is missing or invalid in .env"}

    try:
        model = genai.GenerativeModel('gemini-pro')
        
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
        # Truncate to 10k chars to stay within reasonable limits if file is huge

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean cleanup if model returns markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        return json.loads(response_text)

    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": f"Failed to analyze resume: {str(e)}"}

def extract_search_criteria(text: str) -> dict:
    """
    Extracts criteria for searching external jobs.
    Returns: { "experience_level": str, "domain": str, "top_skills": list, "query": str }
    """
    if not api_key:
        return {"error": "Gemini API Key is missing on Server"}

    try:
        model = genai.GenerativeModel('gemini-pro')
        
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
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        return json.loads(response_text)
        
    except Exception as e:
        print(f"LLM Search Criteria Error: {e}")
        
        # Try to list available models to help debugging
        try:
            available = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available.append(m.name)
            
            return {"error": f"LLM Failed. Error: {str(e)}. AVAILABLE MODELS: {', '.join(available)}"}
        except Exception as list_err:
             return {"error": f"LLM Failed: {str(e)}. Also failed to list models: {str(list_err)}"}
