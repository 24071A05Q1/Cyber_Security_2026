from django.contrib import admin, messages
from django.utils import timezone
from django.core.mail import send_mail
from .models import Job, JobApplication, Interview


# -----------------------
# Custom Filter for "Today"
# -----------------------
class TodayInterviewFilter(admin.SimpleListFilter):
    title = "Today's Interviews"
    parameter_name = 'today_interviews'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'today':
            today = timezone.localdate()
            return queryset.filter(date=today)
        return queryset


# -----------------------
# Job Admin
# -----------------------
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'employer', 'is_active', 'created_at')
    search_fields = ('title', 'company_name', 'employer__username')


# -----------------------
# Job Application Admin
# -----------------------
@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'student', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('job__title', 'student__username')
    actions = ['shortlist_selected']

    @admin.action(description='Shortlist selected applications')
    def shortlist_selected(self, request, queryset):
        updated = 0
        for app in queryset:
            if app.status != 'shortlisted':
                app.status = 'shortlisted'
                app.save()  # triggers send_shortlist_email()
                updated += 1
        self.message_user(request, f"Shortlisted {updated} application(s).", level=messages.SUCCESS)


# -----------------------
# Interview Admin
# -----------------------
@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'scheduled_by', 'round_type', 'date', 'time', 'status')
    list_filter = (TodayInterviewFilter, 'status', 'round_type', 'date')
    search_fields = ('application__student__username', 'application__job__title')

    actions = ['send_today_interview_reminders']

    def get_queryset(self, request):
        """Optimize queries by preloading related objects."""
        qs = super().get_queryset(request)
        return qs.select_related('application__student', 'application__job')

    def send_today_interview_reminders(self, request, queryset):
        today = timezone.localdate()
        interviews_today = queryset.filter(date=today)

        if not interviews_today.exists():
            self.message_user(request, "No interviews scheduled for today.", level='warning')
            return

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
            recipient = [interview.application.student.email]
            send_mail(subject, message, None, recipient)

        self.message_user(request, f"Sent reminders to {interviews_today.count()} students.")

    send_today_interview_reminders.short_description = "Send reminders for today's interviews"
