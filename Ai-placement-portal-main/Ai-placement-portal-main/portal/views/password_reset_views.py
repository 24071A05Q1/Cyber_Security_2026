"""
Custom password reset views that use SITE_DOMAIN setting for proper domain in reset links.
This fixes the issue where reset links use 127.0.0.1:8000 which doesn't work on mobile devices.
"""

from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.conf import settings
from django.urls import reverse_lazy


class CustomPasswordResetForm(PasswordResetForm):
    """Custom form that uses SITE_DOMAIN for email links."""
    
    def save(self, domain_override=None, use_https=False, 
             token_generator=None, from_email=None, request=None, 
             subject_template_name=None, email_template_name=None, 
             html_email_template_name=None, extra_email_context=None):
        """Override save to use SITE_DOMAIN setting."""
        # Get domain from settings if not provided
        if domain_override is None:
            domain_override = getattr(settings, 'SITE_DOMAIN', None)
            if domain_override:
                # Remove protocol if present
                domain_override = domain_override.replace('http://', '').replace('https://', '')
        
        # Get protocol from settings
        if not use_https:
            use_https = getattr(settings, 'SITE_PROTOCOL', 'http') == 'https'
        
        # Call parent save with custom domain
        return super().save(
            domain_override=domain_override,
            use_https=use_https,
            token_generator=token_generator,
            from_email=from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            request=request,
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            html_email_template_name=html_email_template_name,
            extra_email_context=extra_email_context,
        )


class CustomPasswordResetView(auth_views.PasswordResetView):
    """Custom password reset view that uses SITE_DOMAIN setting."""
    
    template_name = 'portal/password_reset.html'
    email_template_name = 'portal/password_reset_email.html'
    subject_template_name = 'portal/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = CustomPasswordResetForm

