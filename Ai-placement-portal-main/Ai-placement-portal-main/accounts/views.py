import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .forms import CustomUserCreationForm
from .models import StudentProfile
from portal.models import Job, JobApplication, ResumeAnalysis
from portal.tasks_ai import parse_and_index_resume


# ----------------------------------------------------
# USER SIGNUP
# ----------------------------------------------------
def signup_view(request):
    """Handles user registration."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'portal/signup.html', {'form': form})


# ----------------------------------------------------
# USER LOGIN
# ----------------------------------------------------
def login_view(request):
    """Handles user login."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')

    return render(request, 'portal/login.html')


# ----------------------------------------------------
# PROFILE UPDATE / RESUME UPLOAD (AI PARSING)
# ----------------------------------------------------
@login_required
def update_profile_view(request):
    """Upload or update resume and trigger AI parsing."""
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')

    if request.method == 'POST':
        uploaded_file = request.FILES.get('resume')
        if uploaded_file:
            student_profile.resume = uploaded_file
            student_profile.save()
            
            # Create or update ResumeAnalysis record
            analysis, created = ResumeAnalysis.objects.get_or_create(
                student=student_profile,
                defaults={'status': 'pending'}
            )
            if not created:
                analysis.status = 'pending'
                analysis.extracted_skills = None
                analysis.recommended_jobs = None
                analysis.save()
            
            messages.success(request, "Resume uploaded successfully! AI parsing started...")
            
            # Run analysis synchronously (without Celery)
            try:
                parse_and_index_resume(student_profile.id)
                messages.success(request, "Resume analysis completed!")
            except Exception as e:
                messages.warning(request, f"Resume uploaded but analysis failed: {str(e)}")
        else:
            messages.warning(request, "Please upload a resume before saving.")

        return redirect('dashboard')

    return render(request, 'portal/update_profile.html', {'student_profile': student_profile})


# ----------------------------------------------------
# STUDENT DASHBOARD (AI-INTEGRATED)
# ----------------------------------------------------
@login_required
def student_dashboard(request):
    """Displays student dashboard with AI job recommendations."""
    user = request.user

    try:
        student_profile = StudentProfile.objects.get(user=user)
        student_profile.refresh_from_db()
    except StudentProfile.DoesNotExist:
        student_profile = None

    # ===================================
    # AI ANALYSIS AND RECOMMENDATIONS
    # ===================================
    ai_status = None
    ai_skills = []
    recommended_jobs = []
    
    if student_profile:
        try:
            # Get the LATEST resume analysis for this student
            resume_analysis = ResumeAnalysis.objects.filter(
                student=student_profile
            ).order_by('-updated_at').first()
            
            print(f"🔍 DEBUG - Found analysis: {resume_analysis is not None}")
            
            if resume_analysis:
                ai_status = resume_analysis.status
                print(f"🔍 DEBUG - AI Status: {ai_status}")
                
                if resume_analysis.status == 'done':
                    # Parse extracted skills
                    if resume_analysis.extracted_skills:
                        ai_skills = resume_analysis.extracted_skills
                        print(f"🔍 DEBUG - Skills: {ai_skills}")
                    
                    # Get AI-matched jobs with scores
                    if resume_analysis.recommended_jobs:
                        job_data = resume_analysis.recommended_jobs
                        print(f"🔍 DEBUG - Job data: {job_data}")
                        
                        # Extract job IDs and scores
                        job_scores = {}
                        if isinstance(job_data, list):
                            for item in job_data:
                                if isinstance(item, dict) and 'job_id' in item:
                                    job_scores[item['job_id']] = item.get('score', 0)
                        
                        print(f"🔍 DEBUG - Job scores: {job_scores}")
                        
                        # Fetch actual job objects
                        if job_scores:
                            jobs = Job.objects.filter(
                                id__in=job_scores.keys(),
                                is_active=True
                            )
                            
                            print(f"🔍 DEBUG - Found {jobs.count()} jobs")
                            
                            recommended_jobs = []
                            for job in jobs:
                                job.match_score = job_scores.get(job.id, 0)
                                recommended_jobs.append(job)
                            
                            # Sort by score
                            recommended_jobs.sort(key=lambda x: x.match_score, reverse=True)
                            
                            print(f"🔍 DEBUG - Recommended jobs count: {len(recommended_jobs)}")
            else:
                print("🔍 DEBUG - No analysis record found")
                ai_status = None
                
        except Exception as e:
            print(f"❌ ERROR loading AI recommendations: {e}")
            import traceback
            traceback.print_exc()
            ai_status = 'error'

    # Get all available jobs
    available_jobs = Job.objects.filter(is_active=True).order_by('-created_at')

    # Get student's applications
    applied_jobs = JobApplication.objects.filter(student=user).select_related('job')

    # Final debug output
    print(f"📊 FINAL CONTEXT:")
    print(f"   - ai_status: {ai_status}")
    print(f"   - ai_skills count: {len(ai_skills)}")
    print(f"   - recommended_jobs count: {len(recommended_jobs)}")

    context = {
        'student_profile': student_profile,
        'ai_status': ai_status,
        'ai_skills': ai_skills,
        'recommended_jobs': recommended_jobs,
        'available_jobs': available_jobs,
        'applied_jobs': applied_jobs,
    }

    return render(request, 'portal/student_dashboard.html', context)


# ----------------------------------------------------
# RE-ANALYZE RESUME (AJAX / CELERY TRIGGER)
# ----------------------------------------------------
@login_required
@require_POST
def reanalyze_resume(request):
    """
    Trigger resume re-analysis manually from dashboard.
    Creates/updates ResumeAnalysis record and runs analysis.
    """
    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Student profile not found.'
        }, status=404)

    if not profile.resume:
        return JsonResponse({
            'status': 'error', 
            'message': 'Please upload your resume before re-analyzing.'
        }, status=400)

    # Create or update ResumeAnalysis record
    analysis, created = ResumeAnalysis.objects.get_or_create(
        student=profile,
        defaults={'status': 'pending'}
    )
    
    if not created:
        analysis.status = 'pending'
        analysis.extracted_skills = None
        analysis.recommended_jobs = None
        analysis.error_message = None
        analysis.save()

    # Run analysis synchronously (without Celery)
    try:
        result = parse_and_index_resume(profile.id)
        if result.get('status') == 'success':
            return JsonResponse({
                'status': 'success', 
                'message': 'Resume re-analysis completed successfully!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result.get('message', 'Analysis failed')
            }, status=500)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error during analysis: {str(e)}'
        }, status=500)