from django.contrib.auth import get_user_model
from accounts.models import StudentProfile, EmployerProfile, CustomUser
from portal.models import Job, JobApplication
from django import forms
from .models import Interview

User = get_user_model()


class StudentRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, help_text='Required. 150 characters or fewer.')
    email = forms.EmailField(help_text='Required. Enter a valid email address.')
    password = forms.CharField(widget=forms.PasswordInput, help_text='Required. Enter a secure password.')
    confirm_password = forms.CharField(widget=forms.PasswordInput, help_text='Required. Confirm your password.')

    class Meta:
        model = StudentProfile
        fields = ['photo', 'name', 'email', 'skills', 'resume', 'phone', 'department', 'graduation_year', 'cgpa']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return confirm_password

    def save(self, commit=True):
        # Create the CustomUser first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            role='student'
        )
        
        # Create the StudentProfile
        student_profile = super().save(commit=False)
        student_profile.user = user
        if commit:
            student_profile.save()
        return student_profile


class EmployerRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = EmployerProfile
        fields = ['company_name', 'contact_number', 'website', 'industry', 'company_size']

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return confirm_password

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            role='employer'
        )
        
        employer_profile = super().save(commit=False)
        employer_profile.user = user
        if commit:
            employer_profile.save()
        return employer_profile


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company_name', 'description', 'requirements', 'location', 'salary_range', 'job_type']


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your cover letter here...'})
        }


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['round_type', 'date', 'time', 'location', 'notes']
