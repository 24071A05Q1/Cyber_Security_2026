from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Job, JobApplication

@login_required
def view_applications(request, job_id):
    """Employer views all applications for a specific job."""
    if request.user.role != "employer":
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    job = get_object_or_404(Job, id=job_id, employer=request.user)
    applications = JobApplication.objects.filter(job=job)
    return render(request, "portal/view_applications.html", {
        "job": job,
        "applications": applications
    })

@login_required
def shortlist_application(request, application_id):
    """Shortlist a candidate."""
    application = get_object_or_404(JobApplication, id=application_id)
    if request.user != application.job.employer and not request.user.is_staff:
        messages.error(request, "You cannot shortlist this application.")
        return redirect("dashboard")

    if application.status != "shortlisted":
        application.status = "shortlisted"
        application.save()
        messages.success(request, f"{application.student.username} has been shortlisted.")
    else:
        messages.info(request, f"{application.student.username} is already shortlisted.")

    return redirect(request.META.get("HTTP_REFERER", "employer_dashboard"))

@login_required
def review_application(request, application_id):
    """Mark an application as under review."""
    application = get_object_or_404(JobApplication, id=application_id)
    application.status = "under_review"
    application.save()
    messages.info(request, f"{application.student.username} is now under review.")
    return redirect(request.META.get("HTTP_REFERER", "employer_dashboard"))

@login_required
def reject_application(request, application_id):
    """Reject a candidate."""
    application = get_object_or_404(JobApplication, id=application_id)
    application.status = "rejected"
    application.save()
    messages.error(request, f"{application.student.username} has been rejected.")
    return redirect(request.META.get("HTTP_REFERER", "employer_dashboard"))
