# portal/tasks_ai.py
import json
import re
from celery import shared_task
from django.utils import timezone
from accounts.models import StudentProfile
from portal.models import Job, ResumeAnalysis


@shared_task(bind=True, max_retries=3)
def parse_and_index_resume(self, student_profile_id):
    """
    Celery task to analyze a student's resume, extract skills,
    match with jobs, and store results in ResumeAnalysis model.
    """
    try:
        profile = StudentProfile.objects.get(id=student_profile_id)

        # Get or create ResumeAnalysis record
        analysis, created = ResumeAnalysis.objects.get_or_create(
            student=profile,
            defaults={'status': 'pending'}
        )

        # Mark as processing
        analysis.status = 'processing'
        analysis.save()

        if not profile.resume:
            analysis.status = 'error'
            analysis.error_message = 'No resume found for this profile.'
            analysis.save()
            return {'status': 'error', 'message': 'No resume found for this profile.'}

        # ------------------------------------------------------------------
        # 🔍 Step 1: Read the resume file (PDF, DOCX, TXT)
        # ------------------------------------------------------------------
        text = ""
        resume_path = profile.resume.path

        if resume_path.lower().endswith(".pdf"):
            from PyPDF2 import PdfReader
            try:
                pdf = PdfReader(resume_path)
                text = " ".join(page.extract_text() or "" for page in pdf.pages)
            except Exception as e:
                text = ""
                print(f"PDF reading error: {e}")
                
        elif resume_path.lower().endswith(".txt"):
            with open(resume_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                
        elif resume_path.lower().endswith(".docx"):
            from docx import Document
            doc = Document(resume_path)
            text = " ".join(p.text for p in doc.paragraphs)
        else:
            text = ""

        if not text.strip():
            analysis.status = 'error'
            analysis.error_message = 'Could not extract text from resume.'
            analysis.save()
            return {'status': 'error', 'message': 'Could not read resume text.'}

        # Store extracted text
        analysis.resume_text = text[:5000]  # Store first 5000 chars

        # ------------------------------------------------------------------
        # 🧩 Step 2: Extract skills using simple keyword matching
        # (You can replace this with NLP/Gemini/OpenAI extraction later)
        # ------------------------------------------------------------------
        KNOWN_SKILLS = [
            "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "HTML", "CSS",
            "Django", "Flask", "FastAPI", "React", "Angular", "Vue", "Node.js", "Express",
            "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Firebase",
            "Data Analysis", "Machine Learning", "Deep Learning", "AI", "NLP",
            "Pandas", "NumPy", "TensorFlow", "Keras", "PyTorch", "Scikit-learn",
            "Git", "GitHub", "Linux", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
            "REST API", "GraphQL", "Microservices", "CI/CD", "Jenkins",
            "Selenium", "Testing", "Agile", "Scrum", "JIRA"
        ]

        text_lower = text.lower()
        found_skills = []
        
        for skill in KNOWN_SKILLS:
            skill_pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(skill_pattern, text_lower):
                found_skills.append(skill)

        found_skills = sorted(set(found_skills))

        # ------------------------------------------------------------------
        # 🎯 Step 3: Match with available jobs
        # ------------------------------------------------------------------
        jobs = Job.objects.filter(is_active=True)
        job_matches = []
        
        for job in jobs:
            score = calculate_match_score(found_skills, job)
            if score > 20:  # Only include jobs with >20% match
                job_matches.append({
                    'job_id': job.id,
                    'score': round(score, 1)
                })
        
        # Sort by score (highest first)
        job_matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Keep top 10 matches
        top_matches = job_matches[:10]

        # ------------------------------------------------------------------
        # 💾 Step 4: Save results to ResumeAnalysis
        # ------------------------------------------------------------------
        if found_skills:
            analysis.extracted_skills = found_skills  # Store as JSON
            analysis.recommended_jobs = top_matches  # Store as JSON
            analysis.status = 'done'
            analysis.error_message = None
        else:
            analysis.extracted_skills = []
            analysis.recommended_jobs = []
            analysis.status = 'done'
            analysis.error_message = 'No skills detected in resume.'

        analysis.save()

        return {
            'status': 'success',
            'skills': found_skills,
            'job_matches': len(top_matches),
            'student': profile.user.username,
            'timestamp': timezone.now().isoformat()
        }

    except StudentProfile.DoesNotExist:
        return {'status': 'error', 'message': f'StudentProfile {student_profile_id} not found.'}

    except Exception as e:
        # Handle fatal errors gracefully
        try:
            analysis = ResumeAnalysis.objects.get(student_id=student_profile_id)
            analysis.status = 'error'
            analysis.error_message = str(e)
            analysis.save()
        except Exception:
            pass
        
        print(f"Error in parse_and_index_resume: {e}")
        return {'status': 'error', 'message': str(e)}


def calculate_match_score(skills, job):
    """
    Calculate match percentage between student skills and job requirements.
    
    Args:
        skills: List of extracted skills from resume
        job: Job object
        
    Returns:
        Float: Match score as percentage (0-100)
    """
    if not skills:
        return 0
    
    # Combine job text fields for matching
    job_text = f"{job.title} {job.description} {job.requirements}".lower()
    
    # Count skill matches
    matches = 0
    for skill in skills:
        skill_pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(skill_pattern, job_text):
            matches += 1
    
    # Calculate percentage
    score = (matches / len(skills)) * 100
    
    return score