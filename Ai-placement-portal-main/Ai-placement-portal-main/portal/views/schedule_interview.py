from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.dateparse import parse_date, parse_time
from portal.models import JobApplication, Interview
from django.contrib.auth.decorators import login_required


@login_required
def schedule_interview(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)

    if request.method == "POST":
        interview_date = request.POST.get("date")   # YYYY-MM-DD
        interview_time = request.POST.get("time")   # HH:MM (24-hour from <input type="time">)

        round_type = request.POST.get("round_type")
        location = request.POST.get("location")
        notes = request.POST.get("notes")

        # Parse date and time properly
        date_obj = parse_date(interview_date)
        time_obj = parse_time(interview_time)

        if not date_obj or not time_obj:
            messages.error(request, "Please provide both date and time.")
            return redirect("schedule_interview", application_id=application_id)

        # Create or update interview
        interview, created = Interview.objects.update_or_create(
            application=application,
            defaults={
                "scheduled_by": request.user,
                "round_type": round_type,
                "date": date_obj,
                "time": time_obj,
                "location": location,
                "notes": notes,
                "status": "scheduled",
            }
        )

        # Send email notification
        interview.send_interview_email()

        application.status = "interview_scheduled"
        application.save()

        messages.success(request, "Interview scheduled successfully.")
        return redirect("view_applications", job_id=application.job.id)

    return render(request, "portal/schedule_interview.html", {"application": application})
