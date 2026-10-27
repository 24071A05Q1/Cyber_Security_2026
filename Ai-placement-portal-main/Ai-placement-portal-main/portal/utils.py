"""
Resume Matching Utility Functions
Automatically matches student resumes with job requirements
"""
import re
from typing import List, Dict, Tuple
from accounts.models import StudentProfile
from portal.models import Job


def normalize_skills(skills_string: str) -> set:
    """
    Normalize and extract skills from a string.
    Handles comma-separated, space-separated, or mixed formats.
    """
    if not skills_string:
        return set()
    
    # Convert to lowercase and split by common delimiters
    skills = re.split(r'[,;|/\n]+', skills_string.lower())
    
    # Clean and strip each skill
    normalized = set()
    for skill in skills:
        skill = skill.strip()
        if skill and len(skill) > 1:  # Ignore single characters
            normalized.add(skill)
    
    return normalized


def extract_skills_from_text(text: str) -> set:
    """
    Extract skills from job requirements or description text.
    Looks for common skill patterns and keywords.
    """
    if not text:
        return set()
    
    # Common technical skills keywords
    common_skills = [
        'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
        'html', 'css', 'react', 'angular', 'vue', 'node.js', 'django', 'flask',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
        'machine learning', 'ml', 'deep learning', 'ai', 'artificial intelligence',
        'data science', 'data analysis', 'statistics',
        'aws', 'azure', 'gcp', 'cloud computing',
        'docker', 'kubernetes', 'devops', 'ci/cd',
        'git', 'github', 'gitlab',
        'agile', 'scrum', 'project management',
        'communication', 'leadership', 'teamwork', 'problem solving'
    ]
    
    text_lower = text.lower()
    found_skills = set()
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.add(skill)
    
    return found_skills


def calculate_skill_match_score(student_skills: set, job_required_skills: set) -> float:
    """
    Calculate skill matching score (0-100).
    Returns percentage of job requirements matched by student.
    """
    if not job_required_skills:
        return 0.0
    
    if not student_skills:
        return 0.0
    
    # Find matching skills
    matched_skills = student_skills.intersection(job_required_skills)
    
    # Calculate percentage
    match_score = (len(matched_skills) / len(job_required_skills)) * 100
    
    return round(match_score, 2)


def calculate_cgpa_score(student_cgpa: float, min_cgpa: float = None) -> float:
    """
    Calculate CGPA score component (0-100).
    If no minimum CGPA specified, gives full score if CGPA exists.
    """
    if student_cgpa is None:
        return 0.0
    
    if min_cgpa is None:
        # If no minimum specified, give score based on CGPA value
        # Scale: 0-10 CGPA -> 0-100 score
        return min(100.0, (student_cgpa / 10.0) * 100)
    
    if student_cgpa >= min_cgpa:
        return 100.0
    
    # Linear scaling if below minimum
    return max(0.0, (student_cgpa / min_cgpa) * 100)


def calculate_department_match(student_dept: str, required_dept: str) -> float:
    """
    Calculate department matching score (0 or 100).
    """
    if not required_dept:
        return 50.0  # Neutral score if no requirement
    
    if not student_dept:
        return 0.0
    
    # Case-insensitive comparison
    if student_dept.lower().strip() == required_dept.lower().strip():
        return 100.0
    
    # Partial match (e.g., "Computer Science" matches "CS")
    if required_dept.lower() in student_dept.lower() or student_dept.lower() in required_dept.lower():
        return 80.0
    
    return 0.0


def calculate_graduation_year_match(student_year: int, required_year: int = None) -> float:
    """
    Calculate graduation year match score.
    """
    if required_year is None:
        return 50.0  # Neutral if no requirement
    
    if student_year is None:
        return 0.0
    
    # Exact match
    if student_year == required_year:
        return 100.0
    
    # Within 1 year (flexible)
    if abs(student_year - required_year) <= 1:
        return 80.0
    
    # Within 2 years
    if abs(student_year - required_year) <= 2:
        return 60.0
    
    return 0.0


def parse_job_requirements(job: Job) -> Dict:
    """
    Parse job requirements to extract matching criteria.
    Returns dict with skills, min_cgpa, department, graduation_year.
    """
    requirements_text = job.requirements.lower()
    
    # Extract skills from requirements
    job_skills = extract_skills_from_text(job.requirements)
    job_skills.update(extract_skills_from_text(job.description))
    
    # Try to extract minimum CGPA (look for patterns like "CGPA: 7.5", "minimum 7.0", etc.)
    min_cgpa = None
    cgpa_patterns = [
        r'cgpa[:\s]+(\d+\.?\d*)',
        r'minimum[:\s]+cgpa[:\s]+(\d+\.?\d*)',
        r'min[:\s]+cgpa[:\s]+(\d+\.?\d*)',
        r'cgpa[:\s]+(\d+\.?\d*)[\s]+and[+\s]+above',
    ]
    for pattern in cgpa_patterns:
        match = re.search(pattern, requirements_text)
        if match:
            try:
                min_cgpa = float(match.group(1))
                break
            except ValueError:
                pass
    
    # Try to extract department requirement
    required_department = None
    dept_patterns = [
        r'department[:\s]+([a-z\s]+)',
        r'degree[:\s]+in[:\s]+([a-z\s]+)',
        r'([a-z\s]+)[\s]+degree',
    ]
    for pattern in dept_patterns:
        match = re.search(pattern, requirements_text)
        if match:
            required_department = match.group(1).strip()
            break
    
    # Try to extract graduation year
    required_year = None
    year_patterns = [
        r'graduation[:\s]+year[:\s]+(\d{4})',
        r'passing[:\s]+year[:\s]+(\d{4})',
        r'year[:\s]+(\d{4})',
    ]
    for pattern in year_patterns:
        match = re.search(pattern, requirements_text)
        if match:
            try:
                required_year = int(match.group(1))
                break
            except ValueError:
                pass
    
    return {
        'skills': job_skills,
        'min_cgpa': min_cgpa,
        'department': required_department,
        'graduation_year': required_year
    }


def match_resume_to_job(job: Job, student_profile: StudentProfile) -> Dict:
    """
    Match a single student's resume/profile to a job.
    Returns dict with match details and total score.
    """
    # Parse job requirements
    job_criteria = parse_job_requirements(job)
    
    # Get student skills
    student_skills = normalize_skills(student_profile.skills or '')
    
    # Calculate individual component scores
    skill_score = calculate_skill_match_score(student_skills, job_criteria['skills'])
    cgpa_score = calculate_cgpa_score(
        float(student_profile.cgpa) if student_profile.cgpa else None,
        job_criteria['min_cgpa']
    )
    dept_score = calculate_department_match(
        student_profile.department or '',
        job_criteria['department'] or ''
    )
    year_score = calculate_graduation_year_match(
        student_profile.graduation_year,
        job_criteria['graduation_year']
    )
    
    # Calculate weighted total score
    # Weights: Skills (60%), CGPA (20%), Department (10%), Year (10%)
    total_score = (
        skill_score * 0.60 +
        cgpa_score * 0.20 +
        dept_score * 0.10 +
        year_score * 0.10
    )
    
    return {
        'student': student_profile,
        'score': round(total_score, 2),
        'skill_score': round(skill_score, 2),
        'cgpa_score': round(cgpa_score, 2),
        'dept_score': round(dept_score, 2),
        'year_score': round(year_score, 2),
        'matched_skills': student_skills.intersection(job_criteria['skills']),
        'missing_skills': job_criteria['skills'] - student_skills,
        'job_criteria': job_criteria
    }


def find_best_matches_for_job(job: Job, limit: int = 20, min_score: float = 30.0) -> List[Dict]:
    """
    Find the best matching students for a given job.
    Returns list of match dictionaries sorted by score (descending).
    
    Args:
        job: Job instance
        limit: Maximum number of matches to return
        min_score: Minimum match score to include (0-100)
    """
    # Get all active students with profiles
    all_students = StudentProfile.objects.filter(user__is_active=True).select_related('user')
    
    matches = []
    
    for student_profile in all_students:
        # Skip if student already applied
        from portal.models import JobApplication
        if JobApplication.objects.filter(job=job, student=student_profile.user).exists():
            continue
        
        # Calculate match
        match_result = match_resume_to_job(job, student_profile)
        
        # Only include if score meets minimum threshold
        if match_result['score'] >= min_score:
            matches.append(match_result)
    
    # Sort by score (descending)
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top N matches
    return matches[:limit]
