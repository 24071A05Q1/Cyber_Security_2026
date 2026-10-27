from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import JobForm, JobApplicationForm
from ..models import Job, JobApplication

@login_required
def post_job(request):
    if request.user.role != "employer":
        return redirect("dashboard")
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()
            messages.success(request, "Job posted!")
            return redirect("employer_dashboard")
    else:
        form = JobForm()
    return render(request, "portal/post_job.html", {"form": form})

@login_required
def apply_job(request, job_id):
    if request.user.role != "student":
        return redirect("dashboard")
    job = get_object_or_404(Job, id=job_id)
    if request.method == "POST":
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.student = request.user
            application.save()
            messages.success(request, "Applied successfully!")
            return redirect("student_dashboard")
    else:
        form = JobApplicationForm()
    return render(request, "portal/apply_job.html", {"job": job, "form": form})

@login_required
def job_details(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    has_applied = JobApplication.objects.filter(job=job, student=request.user).exists()
    return render(request, "portal/job_details.html", {
        "job": job,
        "has_applied": has_applied
    })
