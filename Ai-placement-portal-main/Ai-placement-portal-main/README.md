# 🎓 AI-Powered Placement Portal

A Django-based placement management platform connecting **students,
employers, and administrators** in one application.

The platform supports student profiles and resume uploads, employer job
management, job applications, recruiter workflows, resume text
extraction, skill detection, and automated job recommendations.

> **Important:** The current resume-analysis implementation uses a
> maintained skill vocabulary and keyword matching. The project also
> contains a TF-IDF/cosine-similarity recommendation component. This
> README therefore does not describe the system as a general-purpose LLM
> recruiter.

------------------------------------------------------------------------

## ✨ Project Highlights

-   👨‍🎓 Student registration, profiles, resumes, applications, and
    dashboards
-   🏢 Employer/company management and job posting workflows
-   👨‍💼 Administrative management through Django
-   📄 Resume text extraction from PDF, DOCX, and TXT
-   🧩 Resume skill detection
-   🎯 Candidate/job matching and recommendations
-   ⚙️ Background resume processing with Celery
-   📊 Stored resume-analysis status and results
-   🔎 TF-IDF-based job recommendation support
-   📧 Email/notification workflow support
-   🗄️ MySQL-backed Django application

## 👥 User Roles

### 👨‍🎓 Student

-   Create an account and log in
-   Maintain a student profile
-   Upload a resume
-   Manage profile/skills
-   Browse jobs
-   Apply for jobs
-   View placement/application information
-   Receive supported notifications

### 🏢 Employer / Recruiter

-   Register and manage company information
-   Create job postings
-   View applicants
-   Manage applications
-   Shortlist candidates
-   Use candidate/job matching information
-   Communicate with candidates through supported workflows

### 👨‍💼 Administrator

-   Manage users, students, employers, jobs, and applications
-   Monitor placement data
-   Access Django administration
-   Create/manage administrator accounts
-   Monitor the platform

# 🤖 Resume Analysis & Recommendation

The current pipeline is:

``` text
Resume upload
    ↓
Celery background task
    ↓
PDF / DOCX / TXT text extraction
    ↓
Known-skill detection
    ↓
Active-job matching
    ↓
Match scoring
    ↓
ResumeAnalysis storage
    ↓
Recommended jobs
```

The resume task supports PDF, TXT, and DOCX extraction and stores up to
the first 5,000 characters of extracted text.

Skill extraction currently uses a predefined `KNOWN_SKILLS` list and
regular-expression matching.

Active jobs are scored against detected skills, sorted by score, and the
top matches are stored in the resume-analysis result.

The separate TF-IDF recommender builds a vectorizer from job
title/description text and uses cosine similarity to compare a resume
query with indexed jobs.

## ⚡ Background Processing

Celery handles asynchronous resume processing. The task creates/updates
`ResumeAnalysis`, marks processing status, reads the resume, extracts
skills, calculates job matches, stores results, and handles failures. It
is configured as a retryable task with up to three retries.

## 🧠 TF-IDF Management Command

The repository contains a Django command for building and persisting the
TF-IDF job index:

``` bash
python manage.py build_job_tfidf
```

The command invokes the TF-IDF builder and reports the number of indexed
jobs.

# 🛠️ Technology Stack

### Backend

-   Python
-   Django 4.2+
-   Django ORM
-   Celery
-   Redis
-   MySQL

### Frontend

-   HTML
-   CSS
-   Bootstrap
-   JavaScript
-   Django Templates
-   django-crispy-forms

### NLP / Machine Learning

-   Scikit-learn
-   TF-IDF
-   Cosine similarity
-   Sentence Transformers
-   NLTK
-   spaCy
-   FAISS support

### Document Processing

-   PyPDF2
-   PyMuPDF
-   python-docx
-   Pillow

### Data / Utilities

-   NumPy
-   Pandas
-   python-dotenv

# 📂 Project Structure

``` text
Ai-placement-portal/
│
├── accounts/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── app.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── media/
│   └── photos/
│
├── placement_project/
│   ├── __init__.py
│   ├── celery.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── portal/
│   ├── migrations/
│   ├── templates/
│   ├── views/
│   ├── admin.py
│   ├── apps.py
│   ├── build_tfidf.py
│   ├── forms.py
│   ├── models.py
│   ├── recommender_tfidf.py
│   ├── task.py
│   ├── tasks_ai.py
│   ├── tokens.py
│   ├── urls.py
│   ├── utils.py
│   └── utils_ai.py
│
├── static/
│   └── portal/
│
├── create_admin.py
├── manage.py
├── requirements.txt
├── Start_AI_Placement.bat
├── README.md
└── LICENSE
```

The public repository currently contains `accounts`,
`placement_project`, `portal`, media/static directories, `manage.py`,
`create_admin.py`, `Start_AI_Placement.bat`, `requirements.txt`,
`README.md`, and `LICENSE`.

# 🚀 Installation

## 1. Clone the repository

``` bash
git clone https://github.com/LeutnantMutig/Ai-placement-portal.git
cd Ai-placement-portal
```

This matches the repository's actual GitHub name and URL.

## 2. Create a virtual environment

### Windows

``` powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

``` bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

# 🗄️ Database Configuration

The reviewed Django configuration uses MySQL. Create a local database,
for example:

``` sql
CREATE DATABASE placement_db;
```

Configure the database credentials through environment variables used by
your local settings.

# 🔐 Environment Variables

Create `.env` in the project root:

``` env
DEBUG=True
DJANGO_SECRET_KEY=replace-with-a-local-secret-key

DB_NAME=placement_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
```

The settings load `.env` with `python-dotenv` and support
environment-based secret configuration.

> Keep `.env` out of Git.

# 🧱 Database Migration

``` bash
python manage.py makemigrations
python manage.py migrate
```

For a normal checkout where migration files already exist:

``` bash
python manage.py migrate
```

# 👤 Create an Administrator

### Option 1

``` bash
python create_admin.py
```

### Option 2

``` bash
python manage.py createsuperuser
```

Admin:

``` text
http://127.0.0.1:8000/admin/
```

# ⚡ Celery + Redis

Start Redis locally, then run a Celery worker from the project root:

``` bash
celery -A placement_project worker --loglevel=info
```

On Windows, if required:

``` bash
celery -A placement_project worker --loglevel=info --pool=solo
```

Run Django in another terminal:

``` bash
python manage.py runserver
```

# ▶️ Run the Application

``` bash
python manage.py runserver
```

Open:

``` text
http://127.0.0.1:8000/
```

The repository also contains `Start_AI_Placement.bat` as a Windows
startup helper.

# 📦 Dependency Reference

Keep `requirements.txt` authoritative. The reviewed dependency list
includes the following core packages:

``` text
Django>=4.2,<5.0
Pillow>=10.0.0
django-crispy-forms>=2.0
PyPDF2>=3.0.0
nltk>=3.8.1
scikit-learn
python-dotenv>=1.0.0
sentence-transformers==2.2.2
faiss-cpu==1.7.4
PyMuPDF==1.22.5
python-docx==0.8.11
spacy==3.5.0
scikit-learn==1.3.2
pandas==2.2.2
numpy==1.26.2
celery==5.3.1
redis==4.5.5
```

Do not document packages that are not actually present in
`requirements.txt`.

# 📊 Current Matching Approach

The implementation should be described as four stages:

1.  **Document extraction** --- PDF, DOCX, or TXT to text.
2.  **Skill detection** --- vocabulary/keyword matching.
3.  **Skill-to-job matching** --- compares detected skills against job
    title, description, and requirements.
4.  **TF-IDF recommendation** --- vector similarity between resume text
    and indexed jobs.

This is intentionally more precise than calling the project an
LLM-powered recruiter.

# 🧪 Testing

Run:

``` bash
python manage.py test
```

Manually verify:

1.  Student registration/login
2.  Resume upload
3.  PDF/DOCX/TXT extraction
4.  Skill detection
5.  Resume analysis status
6.  Job matching
7.  Recommendation results
8.  Celery worker
9.  Employer job creation
10. Student job application
11. Admin access

# 📸 Screenshots

Do **not** add placeholder screenshots.

Once real screenshots are committed, use:

``` text
screenshots/
├── student-dashboard.png
├── resume-upload.png
├── resume-analysis.png
├── job-listing.png
├── employer-dashboard.png
└── admin-dashboard.png
```

Then add them to this README using relative paths.

# 🔒 Security

Before public/production deployment:

-   Never commit `.env`
-   Never commit database passwords
-   Never commit API keys or OAuth secrets
-   Use a unique production `DJANGO_SECRET_KEY`
-   Set `DEBUG=False`
-   Configure explicit `ALLOWED_HOSTS`
-   Rotate any credential that has ever been exposed

**Important:** the reviewed settings file contains a development
fallback secret and allows all hosts while `DEBUG=True`.

That fallback must not be used for production.

# ⚠️ Limitations

-   Skill extraction is currently vocabulary/keyword based.
-   Matching scores are heuristic indicators, not hiring decisions.
-   PDF extraction quality depends on the source document.
-   Scanned/image-only PDFs may require OCR.
-   Recommendation quality depends on job descriptions.
-   The system should not be treated as an autonomous recruitment
    decision-maker.

# 🛣️ Future Improvements

-   Transformer-based semantic resume/job matching
-   Better skill/entity extraction
-   Embedding-based candidate ranking
-   FAISS-powered semantic search
-   Explainable recommendation results
-   Recruiter analytics
-   Automated application-status workflows
-   OCR for scanned resumes
-   More automated tests
-   Docker deployment
-   CI/CD
-   Production monitoring

# 👨‍💻 Author

**Chirag Pawar**

GitHub: https://github.com/LeutnantMutig

Portfolio: https://chiragpawar.vercel.app/

LinkedIn: https://www.linkedin.com/in/chiragpawar01/

# 📄 License

This project is licensed under the **MIT License**.

See [`LICENSE`](LICENSE) for details.
