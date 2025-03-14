from flask import Flask, request, jsonify
import PyPDF2
import docx
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import os
from werkzeug.utils import secure_filename

# Download NLTK resources
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("averaged_perceptron_tagger")
nltk.download("maxent_ne_chunker")
nltk.download("words")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload size
app.config["ALLOWED_EXTENSIONS"] = {"pdf", "docx", "doc", "txt"}

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def clean_text(text):
    # Replace multiple tabs and spaces with a single space
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned


# Then modify your extract_text functions to use this cleaning
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return clean_text(text)


def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return clean_text(text)


def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        text = file.read()
    return clean_text(text)


def extract_text(file_path):
    file_extension = file_path.split(".")[-1].lower()
    if file_extension == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_extension == "docx":
        return extract_text_from_docx(file_path)
    elif file_extension == "txt":
        return extract_text_from_txt(file_path)
    else:
        return ""


def extract_name(text):
    try:
        lines = text.split("\n")

        # Check first few lines for potential names
        for line in lines[:5]:  # First 5 lines
            if (
                line
                and not re.search(r"resume|cv|curriculum|email|phone", line.lower())
                and len(line.strip().split()) in [2, 3]
            ):
                return line.strip()

        # NLTK Named Entity Recognition (NER) Fallback
        tokens = nltk.tokenize.word_tokenize(text.split("\n\n")[0])
        tagged = nltk.pos_tag(tokens)
        entities = nltk.chunk.ne_chunk(tagged)

        person_names = []
        for subtree in entities:
            if isinstance(subtree, nltk.tree.Tree) and subtree.label() == "PERSON":
                name = " ".join([leaf[0] for leaf in subtree.leaves()])
                person_names.append(name)

        if person_names:
            return person_names[0]

    except Exception as e:
        print(f"Name extraction error: {e}")

    return "Name not found"


def extract_contact_info(text):
    contact_info = {"email": None, "phone": None, "linkedin": None}

    # Email extraction
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, text)
    if emails:
        contact_info["email"] = emails[0]

    # Phone extraction
    phone_pattern = r"(?:(?:\+\d{1,2}\s*(?:\(\d{1,3}\))?)?)?(?:\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{10})"
    phones = re.findall(phone_pattern, text)
    if phones:
        contact_info["phone"] = phones[0]

    # LinkedIn extraction
    linkedin_pattern = (
        r"(?:linkedin\.com/in/|linkedin\.com/profile/|linkedin\.com/)([a-zA-Z0-9_-]+)"
    )
    linkedin = re.findall(linkedin_pattern, text)
    if linkedin:
        contact_info["linkedin"] = f"linkedin.com/in/{linkedin[0]}"

    return contact_info


def extract_education(text):
    education = []

    # Common education degree keywords
    education_keywords = [
        "bachelor",
        "master",
        "phd",
        "doctor",
        "associate",
        "b.s.",
        "m.s.",
        "b.a.",
        "m.a.",
        "bs",
        "ms",
        "ba",
        "ma",
        "mba",
        "undergraduate",
        "graduate",
        "postgraduate",
        "degree",
        "university",
        "college",
        "institute",
        "school",
        "academy",
        "certification",
    ]

    # Create regex pattern for education
    education_pattern = (
        r"(?i)(?:\d{4}\s*(?:-|to)\s*(?:\d{4}|present|current|now)|\w+\s*\d{4})\s*.*?(?:"
        + "|".join(education_keywords)
        + r").*?(?:\.|$)"
    )

    # Look for sections that might contain education info
    sections = re.split(r"\n\s*\n", text)
    for i, section in enumerate(sections):
        if re.search(r"(?i)education|academic|qualification", section):
            # Extract lines from this section and next section as education might span
            education_text = section
            if i + 1 < len(sections):
                education_text += "\n\n" + sections[i + 1]

            # Find matches using pattern
            matches = re.findall(education_pattern, education_text, re.DOTALL)
            for match in matches:
                education.append(match.strip())

            # If pattern didn't work, extract by lines (backup)
            if not education:
                lines = education_text.split("\n")
                for line in lines:
                    if (
                        any(keyword in line.lower() for keyword in education_keywords)
                        and len(line) > 15
                    ):
                        education.append(line.strip())

    # If still no education found, look for education keywords in the entire text
    if not education:
        for keyword in education_keywords:
            pattern = r"(?i)([^.]*?" + keyword + r"[^.]*\.)"
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.strip()) > 15:  # Reasonable length for education entry
                    education.append(match.strip())

    return education


def extract_experience(text):
    experience = []

    # Common work-related keywords
    work_keywords = [
        "experience",
        "employment",
        "work",
        "job",
        "career",
        "position",
        "role",
        "company",
        "corporation",
        "organization",
        "firm",
        "enterprise",
        "professional",
        "occupation",
    ]

    # Look for sections that might contain work experience
    sections = re.split(r"\n\s*\n", text)

    for i, section in enumerate(sections):
        # Check if this section might be a work experience section
        if any(keyword in section.lower() for keyword in work_keywords):
            # Extract this section and next as work experience might span
            experience_text = section
            if i + 1 < len(sections):
                experience_text += "\n\n" + sections[i + 1]

            # Try to extract date patterns which often indicate job entries
            date_pattern = r"(?i)(?:\d{4}\s*(?:-|to)\s*(?:\d{4}|present|current|now)|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4})"

            # Split by dates
            parts = re.split(date_pattern, experience_text)
            dates = re.findall(date_pattern, experience_text)

            if len(parts) > 1:  # If we have date matches
                current_experience = ""

                # Combine date with following content
                for j in range(min(len(dates), len(parts) - 1)):
                    if j + 1 < len(parts):
                        entry = dates[j] + parts[j + 1]
                        if (
                            len(entry.strip()) > 30
                        ):  # Minimum length to be considered a job entry
                            experience.append(entry.strip())
            else:
                # Fallback: split by bullet points or newlines
                lines = re.split(r"•|\n", experience_text)
                current_entry = ""
                for line in lines:
                    cleaned_line = line.strip()
                    if (
                        re.search(
                            r"(?i)(manager|engineer|developer|analyst|specialist|director|coordinator|consultant)",
                            cleaned_line,
                        )
                        and len(current_entry) > 0
                    ):
                        if len(current_entry) > 30:  # Minimum length
                            experience.append(current_entry.strip())
                        current_entry = cleaned_line
                    else:
                        if current_entry and cleaned_line:
                            current_entry += " " + cleaned_line
                        elif not current_entry and cleaned_line:
                            current_entry = cleaned_line

                if current_entry and len(current_entry) > 30:
                    experience.append(current_entry.strip())

    # If still no experience found, try to find job titles and surrounding text
    if not experience:
        job_titles = [
            "manager",
            "director",
            "supervisor",
            "coordinator",
            "specialist",
            "engineer",
            "developer",
            "programmer",
            "analyst",
            "consultant",
            "associate",
            "assistant",
            "representative",
            "officer",
            "administrator",
        ]

        for title in job_titles:
            pattern = r"(?i)([^.]*?" + title + r"[^.]*\.)"
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.strip()) > 30:  # Reasonable length for job entry
                    experience.append(match.strip())

    return experience


def extract_skills(text):
    # Common skill sections
    skill_headers = [
        "skills",
        "technical skills",
        "core competencies",
        "competencies",
        "proficiencies",
        "qualifications",
        "expertise",
        "abilities",
        "professional skills",
        "technical expertise",
        "technologies",
        "hard skills",
        "soft skills",
        "relevant skills",
        "key skills",
    ]

    # Common technical skills
    technical_skills = [
        "python",
        "java",
        "javascript",
        "js",
        "c\\+\\+",
        "c#",
        "ruby",
        "php",
        "sql",
        "nosql",
        "html",
        "css",
        "react",
        "angular",
        "vue",
        "node",
        "express",
        "django",
        "flask",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "jenkins",
        "git",
        "ci/cd",
        "machine learning",
        "ai",
        "artificial intelligence",
        "deep learning",
        "nlp",
        "data science",
        "data analysis",
        "data visualization",
        "tableau",
        "power bi",
        "hadoop",
        "spark",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "pandas",
        "numpy",
        "agile",
        "scrum",
        "jira",
        "kanban",
        "project management",
        "pmp",
        "linux",
        "unix",
        "windows",
        "macos",
        "networking",
        "security",
        "cyber security",
    ]

    skills = set()

    # Check for skills mentioned in the document
    for skill in technical_skills:
        if re.search(r"\b" + skill + r"\b", text.lower()):
            # Normalize skill name
            normalized_skill = skill.replace("\\", "")
            if normalized_skill == "js":
                normalized_skill = "JavaScript"
            elif normalized_skill == "c\\+\\+":
                normalized_skill = "C++"
            else:
                normalized_skill = normalized_skill.title()
            skills.add(normalized_skill)

    # Try to find a skills section and extract from it
    sections = re.split(r"\n\s*\n", text)
    for section in sections:
        if any(header.lower() in section.lower() for header in skill_headers):
            # Split by common separators and add to skills set
            for separator in [",", "•", "∙", "■", "►", "●", "\n"]:
                if separator in section:
                    for skill_item in section.split(separator):
                        cleaned_skill = skill_item.strip()
                        # Filter out non-skill content
                        if 2 < len(cleaned_skill) < 50 and not re.search(
                            r"(?i)(section|header|skills|proficiencies)", cleaned_skill
                        ):
                            skills.add(cleaned_skill)

    return list(skills)


@app.route("/parse-resume", methods=["POST"])
def parse_resume():
    # Check if file was uploaded
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]

    # Check if filename is empty
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    # Check if file type is allowed
    if not allowed_file(file.filename):
        return (
            jsonify(
                {
                    "success": False,
                    "error": f'File type not allowed. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}',
                }
            ),
            400,
        )

    # Save the file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        # Extract text from the resume
        text = extract_text(file_path)

        # Parse information
        parsed_data = {
            "name": extract_name(text),
            "contact_info": extract_contact_info(text),
            "education": extract_education(text),
            "experience": extract_experience(text),
            "skills": extract_skills(text),
        }

        # Cleanup the file after processing
        os.remove(file_path)

        return jsonify({"success": True, "data": parsed_data})

    except Exception as e:
        # Cleanup the file if an error occurs
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
