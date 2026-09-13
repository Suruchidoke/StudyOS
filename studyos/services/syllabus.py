import google.generativeai as genai
import os
from pypdf import PdfReader
from dotenv import load_dotenv
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_syllabus_structure(pdf_path: str) -> dict:
    # 1. Read PDF
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    # 2. Instruct LLM to strictly return JSON
    prompt = f"""
    Extract the subject name and a list of units/topics from the following syllabus text.
    Return ONLY a valid JSON object matching this exact structure:
    {{
      "subject_name": "Name of Subject",
      "units": [
        {{
          "unit_name": "Unit 1",
          "topics": ["Topic 1", "Topic 2"]
        }}
      ]
    }}
    
    Syllabus Text:
    {text[:8000]} 
    """
    
    model = genai.GenerativeModel('gemini-3.6-flash')
    response = model.generate_content(prompt)
    
    try:
        # Strip out markdown block formatting if the LLM adds it
        raw_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_json)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse LLM response into structured JSON.")