from django.contrib.auth.tokens import PasswordResetTokenGenerator

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Avoid external six dependency by using f-strings / str()
        return f"{user.pk}{timestamp}{user.is_active}"

account_activation_token = EmailVerificationTokenGenerator()
