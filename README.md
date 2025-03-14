# AI Resume Parser API

This project is a Flask-based API that extracts key information from resumes in PDF, DOCX, and TXT formats. It processes resumes to extract name, contact information, education, work experience, and skills using Natural Language Processing (NLP) techniques.

## Features
- Supports resume parsing from PDF, DOCX, and TXT files
- Extracts:
  - Name
  - Contact Information (Email, Phone, LinkedIn)
  - Education Details
  - Work Experience
  - Skills
- Uses NLTK for text processing and Named Entity Recognition (NER)
- Flask-based API with endpoints for file upload and health check

## Requirements
Ensure you have the following installed:
- Python 3.8+
- Flask
- PyPDF2
- python-docx
- nltk
- werkzeug

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/resume-parser.git
   cd resume-parser
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
   - **Parse Resume**
     ```sh
     POST /parse-resume
     ```
     **Request:** Upload a file in `form-data` with the key `file`.
     **Response Example:**
     ```json
     {
         "success": true,
         "data": {
             "name": "John Doe",
             "contact_info": {
                 "email": "johndoe@example.com",
                 "phone": "123 456 7890",
                 "linkedin": "linkedin.com/in/johndoe"
             },
             "education": ["Master's in Computer Science - XYZ University (2015-2017)"],
             "experience": ["Software Engineer - TechCorp Inc. (2018 - Present)"],
             "skills": ["Python", "Machine Learning", "Data Analysis"]
         }
     }
     ```

## File Structure
```
resume-parser/
│-- resume_parser.py            # Main Flask application
│-- requirements.txt  # Required dependencies
│-- uploads/          # Directory for uploaded files
```

## Notes
- Ensure `uploads/` directory exists before running the application.
- Modify `app.config['UPLOAD_FOLDER']` if you wish to store uploaded files elsewhere.

## License
This project is licensed under the MIT License.

