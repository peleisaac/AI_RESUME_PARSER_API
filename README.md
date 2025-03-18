# AI Resume Parser API

This project is a Flask-based API that extracts key information from resumes in PDF and DOCX formats. It processes resumes to extract name, contact information, education, work experience, and skills using Natural Language Processing (NLP) techniques.

## Features
- Supports resume parsing from PDF and DOCX files
- Extracts:
  - Name
  - Contact Information (Email, Phone, LinkedIn)
  - Education Details
  - Work Experience
  - Skills
- Uses Google Generative AI for handling resume parsing and ranking whiles fastAPI for fetching APIs
- Uvicorn for Webserving
- Flask-based API with endpoints for file upload and health check

## Requirements
Ensure you have the following installed:
- fastapi==0.109.2
- uvicorn==0.27.1
- python-multipart==0.0.9
- google-generativeai==0.7.0
- python-dotenv==1.0.1
 

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/AI_RESUME_PARSER_API.git
   cd AI_RESUME_PARSER_API
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Download NLTK resources:
   ```sh
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words')"
   ```

## Usage
1. Run the Flask server:
   ```sh
   python app.py
   ```
2. API Endpoints:
   - **Health Check**
     ```sh
     GET /health
     ```
     **Response:**
     ```json
     {"status": "healthy", "version": "1.0.0"}
     ```
   - **Ranking of CVs**
     ```sh
     POST /rank-cvs
     ```
     **Response:**
     ```json
     {
      "ranked_cvs": [
            {
                "id": "candidate1",
                "match_percentage": 85.0,
            },
            {
                "id": "candidate2",
                "match_percentage": 75.0,
            },
       ]
    }
   - **Parse Resume**
     ```
     ```sh
     POST /parse-resume
     ```
     **Request:** Upload a file in `form-data` with the key `file`.
     **Response Example:**
     ```json
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
     ```

## File Structure
```
│-- api.py            # Handling Matching of CVs against requirement of the Employer
│-- app.py            # Main Flask application
│-- requirements.txt  # Required dependencies
│-- .env  # Contains the GOOGLE API Key which is needed by the application for Resume Parsing
```

## Note
- Ranking can only be attained by running api.py

