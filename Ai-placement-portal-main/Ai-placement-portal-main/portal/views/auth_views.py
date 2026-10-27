from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from accounts.models import CustomUser
from ..forms import StudentRegistrationForm, EmployerRegistrationForm
from ..tokens import account_activation_token

User = get_user_model()

def start(request):
    return render(request, "portal/start.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.is_active:
                messages.error(request, "Please verify your email before logging in.")
                return redirect("login")
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "portal/login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("start")

def student_registration(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            student_profile = form.save()
            created_user = student_profile.user
            created_user.is_active = True
            created_user.save()
            messages.success(request, "Registration successful!")
            return redirect("login")
    else:
        form = StudentRegistrationForm()
    return render(request, "portal/student_registration.html", {"form": form})

def employer_registration(request):
    if request.method == "POST":
        form = EmployerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            employer_profile = form.save()
            created_user = employer_profile.user
            created_user.is_active = True
            created_user.save()
            messages.success(request, "Registration successful!")
            return redirect("login")
    else:
        form = EmployerRegistrationForm()
    return render(request, "portal/employer_registration.html", {"form": form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Account activated!")
        return redirect("login")
    return render(request, "portal/email_verification_failed.html")
