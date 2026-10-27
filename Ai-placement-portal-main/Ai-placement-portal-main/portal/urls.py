from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from accounts.views import reanalyze_resume
from . import views  # imports everything from views/__init__.py
from .views.password_reset_views import CustomPasswordResetView
from accounts.views import reanalyze_resume

urlpatterns = [
    # ---------------- Public ----------------
    path('', views.start, name='start'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/student/', views.student_registration, name='student_registration'),
    path('register/employer/', views.employer_registration, name='employer_registration'),

    # ---------------- Dashboards ----------------
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/reanalyze-resume/', reanalyze_resume, name='reanalyze_resume'),
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # ---------------- Job Management ----------------
    path('job/post/', views.post_job, name='post_job'),
    path('job/<int:job_id>/', views.job_details, name='job_details'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/applications/', views.view_applications, name='view_applications'),

    # ---------------- Application Actions ----------------
    path('application/<int:application_id>/shortlist/', views.shortlist_application, name='shortlist_application'),
    path('application/<int:application_id>/review/', views.review_application, name='review_application'),
    path('application/<int:application_id>/reject/', views.reject_application, name='reject_application'),

    # ---------------- Interview Scheduling ----------------
    path('application/<int:application_id>/schedule/', views.schedule_interview, name='schedule_interview'),

    # ---------------- Auto Resume Matching ----------------
    path('job/<int:job_id>/matches/', views.find_job_matches, name='find_job_matches'),

    # ---------------- AI Resume Upload ----------------
    # ✅ Added route for student resume upload / AI auto-parsing
    # path('profile/update/', views.update_profile_view, name='update_profile'),

    # ---------------- Password Reset (Forgot Password) ----------------
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='portal/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='portal/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='portal/password_reset_complete.html'
    ), name='password_reset_complete'),
]


