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
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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
