"""
Generates the dummy resumes in the resumes folder (txt, pdf and docx).
All names and details are made up.

Run once:  python make_sample_data.py
"""

import os

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

RESUME_DIR = "resumes"

# (file name, resume text). The extension decides which format gets written.
RESUMES = [
    (
        "resume_john_doe.pdf",
        """John Doe
Backend Developer | john.doe@example.com | Pune, India

SUMMARY
Backend developer with 4 years of Python experience building REST APIs and data pipelines.

SKILLS
Python, Flask, FastAPI, PostgreSQL, Docker, AWS, Git

EXPERIENCE
Software Engineer, Brightline Systems (2022 - Present)
- Built FastAPI services handling 2 million requests per day
- Cut report generation time by 40 percent by rewriting slow SQL queries
- Wrote unit tests with pytest and set up CI with GitHub Actions

Junior Developer, CodeNest (2020 - 2022)
- Maintained Flask apps and fixed production bugs
- Automated daily data imports using Python scripts

EDUCATION
B.Tech in Computer Science, Pune University, 2020""",
    ),
    (
        "resume_priya_sharma.docx",
        """Priya Sharma
Data Scientist | priya.sharma@example.com | Bengaluru, India

SUMMARY
Data scientist with 3 years of experience in machine learning and analytics. Strong Python and SQL skills.

SKILLS
Python, pandas, scikit-learn, PyTorch, SQL, Tableau, Statistics

EXPERIENCE
Data Scientist, Northwind Analytics (2023 - Present)
- Built a churn prediction model that improved retention campaigns by 18 percent
- Created Tableau dashboards used by the sales leadership team
- Experimented with LLM based text classification using Python

Data Analyst, RetailHub (2021 - 2023)
- Cleaned and analysed customer data with pandas
- Presented weekly insights to the marketing team

EDUCATION
M.Sc. in Statistics, Delhi University, 2021""",
    ),
    (
        "resume_amit_verma.txt",
        """Amit Verma
Frontend Developer | amit.verma@example.com | Jaipur, India

SUMMARY
Frontend developer with 5 years of experience creating fast and accessible web apps.

SKILLS
JavaScript, TypeScript, React, Next.js, HTML, CSS, Jest

EXPERIENCE
Senior Frontend Developer, PixelCraft (2021 - Present)
- Led the migration of a legacy jQuery app to React
- Improved page load speed by 55 percent with code splitting
- Mentored two junior developers

Frontend Developer, WebWorks (2019 - 2021)
- Built reusable component libraries
- Wrote end to end tests

EDUCATION
BCA, Rajasthan University, 2019""",
    ),
    (
        "resume_sara_khan.pdf",
        """Sara Khan
Machine Learning Engineer | sara.khan@example.com | Hyderabad, India

SUMMARY
ML engineer with 2 years of experience deploying NLP models. Comfortable with Python and cloud tools.

SKILLS
Python, PyTorch, Hugging Face, LangChain, FastAPI, Docker, GCP

EXPERIENCE
ML Engineer, Lumen AI (2024 - Present)
- Fine tuned transformer models for document classification
- Built a retrieval augmented generation prototype for internal search
- Deployed models as FastAPI services on GCP

ML Intern, DataSpark (2023 - 2024)
- Labelled and cleaned text data
- Trained baseline models in Python

EDUCATION
B.E. in Information Technology, Osmania University, 2023""",
    ),
    (
        "resume_rahul_mehta.docx",
        """Rahul Mehta
DevOps Engineer | rahul.mehta@example.com | Mumbai, India

SUMMARY
DevOps engineer with 6 years of experience in cloud infrastructure and automation.

SKILLS
Kubernetes, Terraform, AWS, Jenkins, Bash, Python, Prometheus

EXPERIENCE
Lead DevOps Engineer, CloudBridge (2020 - Present)
- Managed Kubernetes clusters running 60 microservices
- Reduced cloud costs by 30 percent through right sizing
- Wrote Python scripts to automate backups and alerts

DevOps Engineer, InfraSoft (2018 - 2020)
- Built CI/CD pipelines in Jenkins
- Set up monitoring with Prometheus and Grafana

EDUCATION
B.Tech in Electronics, Mumbai University, 2018""",
    ),
    (
        "resume_neha_gupta.txt",
        """Neha Gupta
Java Developer | neha.gupta@example.com | Chennai, India

SUMMARY
Java developer with 7 years of experience in enterprise banking applications.

SKILLS
Java, Spring Boot, Hibernate, MySQL, Kafka, JUnit

EXPERIENCE
Senior Java Developer, FinServe (2019 - Present)
- Designed payment microservices using Spring Boot and Kafka
- Led a team of four developers
- Improved test coverage from 45 to 85 percent

Java Developer, BankTech (2016 - 2019)
- Developed back office reporting tools
- Fixed performance issues in Hibernate queries

EDUCATION
B.E. in Computer Science, Anna University, 2016""",
    ),
    (
        "resume_vikram_singh.pdf",
        """Vikram Singh
Full Stack Developer | vikram.singh@example.com | Gurugram, India

SUMMARY
Full stack developer with 3 years of experience. Uses Python on the backend and React on the frontend.

SKILLS
Python, Django, React, PostgreSQL, Redis, REST APIs

EXPERIENCE
Full Stack Developer, ShopSphere (2022 - Present)
- Built an inventory management system with Django and React
- Added Redis caching that cut API response time in half
- Integrated a payment gateway

Intern, StartHub (2021 - 2022)
- Fixed bugs in a Django app
- Wrote API documentation

EDUCATION
B.Tech in Computer Science, GGSIPU, 2021""",
    ),
    (
        "resume_anita_roy.docx",
        """Anita Roy
UX Designer | anita.roy@example.com | Kolkata, India

SUMMARY
UX designer with 4 years of experience designing mobile and web products. Some HTML and CSS knowledge.

SKILLS
Figma, User Research, Prototyping, Wireframing, Design Systems, HTML, CSS

EXPERIENCE
UX Designer, AppForge (2022 - Present)
- Redesigned the onboarding flow and raised sign up completion by 25 percent
- Ran usability tests with 30 participants
- Maintained the company design system

Visual Designer, Studio Nine (2020 - 2022)
- Created marketing assets and landing pages
- Worked closely with developers on handoff

EDUCATION
B.Des, NID Ahmedabad, 2020""",
    ),
]


def write_txt(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def write_docx(path: str, text: str) -> None:
    document = Document()
    for line in text.split("\n"):
        document.add_paragraph(line)
    document.save(path)


def write_pdf(path: str, text: str) -> None:
    pdf = canvas.Canvas(path, pagesize=A4)
    _, page_height = A4
    y = page_height - 60

    for line in text.split("\n"):
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, line)
        y -= 14

    pdf.save()


WRITERS = {".txt": write_txt, ".docx": write_docx, ".pdf": write_pdf}


def main() -> None:
    os.makedirs(RESUME_DIR, exist_ok=True)

    for file_name, text in RESUMES:
        extension = os.path.splitext(file_name)[1]
        WRITERS[extension](os.path.join(RESUME_DIR, file_name), text)
        print("created", file_name)


if __name__ == "__main__":
    main()
