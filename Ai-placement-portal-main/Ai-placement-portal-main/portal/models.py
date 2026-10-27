from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


# -----------------------
# Job Model
# -----------------------
class Job(models.Model):
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_jobs'
    )
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=100)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(
        max_length=50,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('internship', 'Internship'),
            ('contract', 'Contract'),
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"


# -----------------------
# Job Application Model
# -----------------------
class JobApplication(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications'
    )
    cover_letter = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('reviewed', 'Reviewed'),
            ('shortlisted', 'Shortlisted'),
            ('rejected', 'Rejected'),
            ('accepted', 'Accepted'),
            ('interview_scheduled', 'Interview Scheduled'),
        ],
        default='pending'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------------------------
    # New AI/ML Fields
    # ---------------------------
    score = models.FloatField(
        null=True,
        blank=True,
        help_text="Auto-calculated AI relevance score between student resume and job"
    )
    auto_shortlisted = models.BooleanField(
        default=False,
        help_text="Automatically marked if AI score exceeds threshold"
    )

    class Meta:
        unique_together = ['job', 'student']
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.student.username} - {self.job.title}"

    def save(self, *args, **kwargs):
        """Trigger AI scoring and send email when shortlisted."""
        if self.pk:
            old_status = JobApplication.objects.get(pk=self.pk).status
            # ✅ Email when manually shortlisted
            if old_status != 'shortlisted' and self.status == 'shortlisted':
                self.send_shortlist_email()
        super().save(*args, **kwargs)

    def send_shortlist_email(self):
        """Send email when student is shortlisted."""
        subject = f"Shortlisted for {self.job.title} at {self.job.company_name}"
        message = (
            f"Hello {self.student.username},\n\n"
            f"Congratulations! You have been shortlisted for the job '{self.job.title}' at {self.job.company_name}.\n"
            "The employer will contact you soon with further details.\n\n"
            "Best of luck!"
        )
        send_mail(subject, message, None, [self.student.email])


# -----------------------
# Interview Model
# -----------------------
class Interview(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='interview'
    )
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interviews_created',
        null=True,
        blank=True
    )
    round_type = models.CharField(
        max_length=50,
        choices=[
            ('HR', 'HR Round'),
            ('Technical', 'Technical Round'),
            ('Final', 'Final Round'),
        ],
        blank=True,
        null=True
    )
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def date_time(self):
        if self.date and self.time:
            return timezone.make_aware(
                timezone.datetime.combine(self.date, self.time)
            )
        return None

    @property
    def formatted_time(self):
        return self.time.strftime("%I:%M %p") if self.time else None

    def __str__(self):
        return f"Interview for {self.application.student.username} - {self.application.job.title}"

    def send_interview_email(self):
        date_str = self.date.strftime("%d %B %Y") if self.date else "TBA"
        time_str = self.formatted_time or "TBA"
        subject = f"Interview Scheduled for {self.application.job.title}"
        message = (
            f"Hello {self.application.student.username},\n\n"
            f"Your interview for the job '{self.application.job.title}' at {self.application.job.company_name} "
            f"has been scheduled.\n"
            f"Date: {date_str}\n"
            f"Time: {time_str}\n"
            f"Location: {self.location or 'To be decided'}\n\n"
            "Best of luck!"
        )
        send_mail(subject, message, None, [self.application.student.email])


# ===================================
# 🔥 NEW: Resume Analysis Model
# ===================================
class ResumeAnalysis(models.Model):
    """
    Store AI resume analysis results for each student
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('error', 'Error'),
    ]
    
    student = models.OneToOneField(
        'accounts.StudentProfile',  # Reference to StudentProfile in accounts app
        on_delete=models.CASCADE,
        related_name='resume_analysis'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text="Current status of resume analysis"
    )
    extracted_skills = models.JSONField(
        null=True, 
        blank=True,
        help_text="List of skills extracted from resume by AI"
    )
    recommended_jobs = models.JSONField(
        null=True, 
        blank=True,
        help_text="List of recommended job IDs with match scores"
    )
    resume_text = models.TextField(
        null=True,
        blank=True,
        help_text="Extracted text from PDF resume"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error details if analysis failed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Resume Analysis"
        verbose_name_plural = "Resume Analyses"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.student.name} - {self.status} - {self.updated_at.strftime('%Y-%m-%d %H:%M')}"