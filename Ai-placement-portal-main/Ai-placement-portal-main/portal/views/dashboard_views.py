from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import StudentProfile, EmployerProfile, CustomUser
from ..models import Job, JobApplication

@login_required
def dashboard(request):
    if request.user.role == "student":
        return redirect("student_dashboard")
    elif request.user.role == "employer":
        return redirect("employer_dashboard")
    elif request.user.role == "admin":
        return redirect("admin_dashboard")
    messages.error(request, "Invalid role.")
    return redirect("start")

@login_required
def student_dashboard(request):
    if request.user.role != "student":
        return redirect("dashboard")
    profile = request.user.student_profile
    available_jobs = Job.objects.filter(is_active=True)
    applications = JobApplication.objects.filter(student=request.user)
    return render(request, "portal/student_dashboard.html", {
        "student_profile": profile,
        "available_jobs": available_jobs,
        "my_applications": applications
    })

@login_required
def employer_dashboard(request):
    if request.user.role != "employer":
        return redirect("dashboard")
    profile = request.user.employer_profile
    posted_jobs = Job.objects.filter(employer=request.user)
    total_applications = JobApplication.objects.filter(job__employer=request.user).count()
    return render(request, "portal/employer_dashboard.html", {
        "employer_profile": profile,
        "posted_jobs": posted_jobs,
        "total_applications": total_applications
    })

@login_required
def admin_dashboard(request):
    if request.user.role != "admin":
        return redirect("dashboard")
    return render(request, "portal/admin_dashboard.html", {
        "total_students": CustomUser.objects.filter(role="student").count(),
        "total_employers": CustomUser.objects.filter(role="employer").count(),
        "total_jobs": Job.objects.count(),
        "total_applications": JobApplication.objects.count(),
    })
