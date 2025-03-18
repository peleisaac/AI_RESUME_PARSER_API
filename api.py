import os
import json
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai
 
# Initialize FastAPI
app = FastAPI(title="CV Ranking API")
 
# Load environment variables
load_dotenv()
 
# Configure Google AI
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
 
 
# Models
class CV(BaseModel):
    id: str
    content: str
 
 
class JobDescription(BaseModel):
    title: str
    responsibilities: List[str]
    requirements: List[str]
 
 
class RankingRequest(BaseModel):
    job_description: JobDescription
    cvs: List[CV]
 
 
class RankedCV(BaseModel):
    id: str
    match_percentage: float
    strengths: List[str]
    weaknesses: List[str]
 
 
class RankingResponse(BaseModel):
    ranked_cvs: List[RankedCV]
 
 
# Helper functions
def analyze_cv(cv_content: str, job_description: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Google AI to analyze a CV against a job description
    """
    prompt = f"""
    You are an expert HR recruiter. Analyze this CV against the job requirements.
    
    Job Title: {job_description['title']}
    
    Job Responsibilities:
    {' '.join(['- ' + r for r in job_description['responsibilities']])}
    
    Job Requirements:
    {' '.join(['- ' + r for r in job_description['requirements']])}
    
    CV Content:
    {cv_content}
    
    Provide the following in JSON format:
    1. match_percentage: A score from 0-100 indicating overall match
    2. strengths: List of top 3 strengths relevant to this position
    3. weaknesses: List of top 3 missing qualifications or weaknesses
    """
 
    # Create the model instance - using the latest gemini model
    model = genai.GenerativeModel("gemini-1.5-pro")
 
    # Configure generation parameters
    generation_config = {
        "temperature": 0.2,
        "top_k": 40,
        "top_p": 0.95,
        "max_output_tokens": 1024,
    }
 
    # Generate content
    try:
        response = model.generate_content(prompt, generation_config=generation_config)
 
        analysis_text = response.text
 
        # Handle the case where the text might include explanation before or after the JSON
        json_start = analysis_text.find("{")
        json_end = analysis_text.rfind("}") + 1
 
        if json_start >= 0 and json_end > json_start:
            json_str = analysis_text[json_start:json_end]
            analysis = json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in response")
 
        return analysis
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google AI API error: {str(e)}")
 
 
# API Endpoints
@app.post("/rank-cvs", response_model=RankingResponse)
async def rank_cvs(request: RankingRequest = Body(...)):
    """
    Rank multiple CVs based on job description
    """
    if not api_key:
        raise HTTPException(status_code=500, detail="Google AI API key not configured")
 
    job_desc_dict = request.job_description.model_dump()
    results = []
 
    for cv in request.cvs:
        try:
            analysis = analyze_cv(cv.content, job_desc_dict)
            ranked_cv = RankedCV(
                id=cv.id,
                match_percentage=float(analysis["match_percentage"]),
                strengths=analysis["strengths"],
                weaknesses=analysis["weaknesses"],
            )
            results.append(ranked_cv)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error analyzing CV {cv.id}: {str(e)}"
            )
 
    # Sort by match percentage in descending order
    results.sort(key=lambda x: x.match_percentage, reverse=True)
 
    return RankingResponse(ranked_cvs=results)
 
 
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}
 
 
if __name__ == "__main__":
    import uvicorn
 
    uvicorn.run(app, host="0.0.0.0", port=8000)
