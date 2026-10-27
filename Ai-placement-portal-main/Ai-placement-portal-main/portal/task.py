import schedule
import time
from django.utils import timezone
from django.core.mail import send_mail
from .models import Interview
from portal.tasks import run_scheduler # type: ignore


run_scheduler()


def send_today_interview_reminders_job():
    today = timezone.localdate()
    interviews_today = Interview.objects.filter(date=today)

    for interview in interviews_today:
        date_str = interview.date.strftime("%d %B %Y") if interview.date else "TBA"
        time_str = interview.time.strftime("%I:%M %p") if interview.time else "TBA"

        subject = f"Reminder: Interview for {interview.application.job.title} Today"
        message = (
            f"Hello {interview.application.student.username},\n\n"
            f"This is a reminder for your interview scheduled today.\n"
            f"Date: {date_str}\n"
            f"Time: {time_str}\n"
            f"Location: {interview.location or 'To be decided'}\n\n"
            "Good luck!"
        )
        send_mail(subject, message, None, [interview.application.student.email])

    print(f"Sent reminders to {interviews_today.count()} students.")


def run_scheduler():
    schedule.every().day.at("08:00").do(send_today_interview_reminders_job)

    while True:
        schedule.run_pending()
        time.sleep(60)
