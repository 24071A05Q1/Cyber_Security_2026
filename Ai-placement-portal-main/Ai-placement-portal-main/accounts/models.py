from django.db import models  # type: ignore
from django.contrib.auth.models import AbstractUser  # type: ignore
from django.conf import settings  # type: ignore


# -----------------------
# Custom User Model
# -----------------------
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('employer', 'Employer'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"


# -----------------------
# Student Profile Model
# -----------------------
class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    # existing field (basic skills entered manually)
    skills = models.CharField(max_length=255, blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    cgpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    
    # DEPRECATED: These fields are now handled by ResumeAnalysis model in portal app
    # Keeping them for backward compatibility, but not actively used
    ai_skills = models.TextField(blank=True, null=True, help_text="DEPRECATED: Use ResumeAnalysis model")
    ai_status = models.CharField(max_length=50, default="pending", help_text="DEPRECATED: Use ResumeAnalysis model")

    # ---------------------------
    # New AI/ML-related fields
    # ---------------------------
    resume_text = models.TextField(
        null=True,
        blank=True,
        help_text="Extracted text content from the uploaded resume"
    )
    parsed_skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of detected skills extracted from the resume"
    )
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text="Numerical vector representation for AI matching"
    )

    def __str__(self):
        return f"{self.name} ({self.user.username})"


# -----------------------
# Employer Profile Model
# -----------------------
class EmployerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employer_profile'
    )
    company_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=15)
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    company_size = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"


# -----------------------
# Admin Profile Model
# -----------------------
class AdminProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.department}"