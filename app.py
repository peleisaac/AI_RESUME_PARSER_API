# app.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import tempfile
 
# Load environment variables
load_dotenv()
 
# Get API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise EnvironmentError("GOOGLE_API_KEY is not set in environment variables")
 
# Configure Google AI
genai.configure(api_key=api_key)
 
app = FastAPI(
    title="Resume Parser API",
    description="API to parse resume files and extract structured data",
)
 
 
@app.post("/parse-resume/")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF, DOCX) and get structured data in return.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
 
    # Check file extension
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=400, detail="Only PDF and DOCX files are supported"
        )
 
    # Read file content
    file_content = await file.read()
 
    try:
        # Parse resume
        parsed_data = await parse_resume(file_content, file_extension)
        return JSONResponse(content=parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")
 
 
async def parse_resume(file_content: bytes, file_extension: str):
    """
    Parse a resume file and extract structured data.
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(
        suffix=f".{file_extension}", delete=False
    ) as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
 
    try:
        # Set up the model
        model = genai.GenerativeModel("gemini-1.5-pro")
 
        # Prepare the prompt
        prompt = """
        Extract and structure the content of this resume with high accuracy. IMPORTANT RULES:
        1. ONLY include information that is explicitly present in the document - do not make assumptions or fill in details that aren't there
        2. Each piece of information should appear exactly ONCE - do not repeat or duplicate content
        3. If a section or field is not found, use: empty array [] for array fields, 'Unknown' for missing text fields, empty string for descriptions
        4. For dates: use 'Present' only if explicitly indicated as current, otherwise use 'Unknown' for missing dates
        5. Extract text exactly as it appears - do not rephrase or embellish
        6. If you're unsure about any information, mark it as 'Unknown' rather than guessing
        7. Pay special attention to any "RESPONSIBILITIES" or "SIGNIFICANCE" sections in the document and extract them accordingly
        
        Return the data in this JSON format:
        {
            "name": "string",
            "email": "string",
            "phone": "string",
            "address": "string",
            "objective": "string",
            "capabilities": ["string"],
            "responsibilities": ["string"],
            "significance": ["string"],
            "experience": [
                {
                    "company": "string",
                    "title": "string",
                    "startDate": "string",
                    "endDate": "string",
                    "description": "string",
                    "responsibilities": ["string"],
                    "significance": ["string"]
                }
            ],
            "education": [
                {
                    "school": "string",
                    "degree": "string",
                    "startDate": "string",
                    "endDate": "string",
                    "description": "string"
                }
            ],
            "skills": ["string"],
            "certificates": ["string"],
            "workshops": ["string"],
            "languages": ["string"],
            "interests": ["string"],
            "projects": [
                {
                    "name": "string",
                    "description": "string",
                    "startDate": "string",
                    "endDate": "string",
                    "technologies": ["string"]
                }
            ],
            "references": [
                {
                    "name": "string",
                    "title": "string",
                    "company": "string",
                    "contact": "string"
                }
            ]
        }
        """
 
        # Process the file
        with open(temp_file_path, "rb") as f:
            if file_extension == "pdf":
                mime_type = "application/pdf"
            else:
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
 
            response = model.generate_content(
                [prompt, {"mime_type": mime_type, "data": f.read()}]
            )
 
        # Extract JSON from response
        result_text = response.text
 
        # Find JSON in the response (sometimes the model wraps it in code blocks)
        json_start = result_text.find("{")
        json_end = result_text.rfind("}") + 1
 
        if json_start == -1 or json_end == 0:
            raise ValueError("Could not find valid JSON in the response")
 
        json_str = result_text[json_start:json_end]
 
        # Parse the JSON
        parsed_data = json.loads(json_str)
 
        # Basic validation
        required_fields = [
            "name",
            "email",
            "phone",
            "address",
            "objective",
            "capabilities",
            "responsibilities",
            "significance",
            "experience",
            "education",
            "skills",
            "certificates",
            "workshops",
            "languages",
            "interests",
            "projects",
            "references",
        ]
 
        for field in required_fields:
            if field not in parsed_data:
                if field in [
                    "experience",
                    "education",
                    "skills",
                    "certificates",
                    "workshops",
                    "languages",
                    "interests",
                    "projects",
                    "references",
                    "capabilities",
                ]:
                    parsed_data[field] = []
                else:
                    parsed_data[field] = "Unknown"
 
        return parsed_data
 
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
 
 
@app.get("/")
async def root():
    return {
        "message": "Resume Parser API is running. Send a POST request to /parse-resume/ with a resume file."
    }
 
 
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
