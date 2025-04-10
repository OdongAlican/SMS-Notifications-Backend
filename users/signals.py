# Signal to check password reusability
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import PrideUser, PasswordHistory
from django.utils import timezone
from datetime import timedelta

@receiver(pre_save, sender=PrideUser)
def check_password_reusability(sender, instance, **kwargs):
    """Ensure a user can't reuse their previous password within 160 days."""
    if instance.pk:  # Ensure the user is already saved (not a new user)
        # Check the password history for the user
        recent_passwords = PasswordHistory.objects.filter(user=instance).order_by('-created_at')[:5]

        for password_entry in recent_passwords:
            # Compare the new password with the old ones
            if instance.password == password_entry.password:
                if timezone.now() - password_entry.created_at < timedelta(days=160):
                    raise ValueError("You cannot reuse a password that was used in the last 160 days.")
