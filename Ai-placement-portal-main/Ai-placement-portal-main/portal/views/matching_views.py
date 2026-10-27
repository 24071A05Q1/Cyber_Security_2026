"""
Views for Auto Resume Matching Feature
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from portal.models import Job
from portal.utils import find_best_matches_for_job


@login_required
def find_job_matches(request, job_id):
    """
    Find and display best matching students for a specific job.
    Only accessible by the job's employer or admins.
    """
    job = get_object_or_404(Job, id=job_id)
    
    # Check permissions
    if request.user.role != "employer" and request.user.role != "admin":
        messages.error(request, "Access denied. Only employers can view job matches.")
        return redirect("dashboard")
    
    if request.user.role == "employer" and job.employer != request.user:
        messages.error(request, "You can only view matches for your own job postings.")
        return redirect("employer_dashboard")
    
    # Get minimum score from query parameter (default: 30%)
    min_score = float(request.GET.get('min_score', 30.0))
    limit = int(request.GET.get('limit', 20))
    
    # Find matches
    matches = find_best_matches_for_job(job, limit=limit, min_score=min_score)
    
    return render(request, "portal/job_matches.html", {
        "job": job,
        "matches": matches,
        "min_score": min_score,
        "total_matches": len(matches)
    })

